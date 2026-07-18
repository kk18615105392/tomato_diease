"""热力图：优先基于 YOLO 检测框生成关注区域；回退 ResNet Grad-CAM / 显著性。"""

from __future__ import annotations

import base64
import io


def _fallback_saliency(image_path: str) -> str:
    from PIL import Image, ImageFilter
    import numpy as np

    img = Image.open(image_path).convert("RGB").resize((224, 224))
    gray = img.convert("L").filter(ImageFilter.GaussianBlur(radius=2))
    arr = np.array(gray, dtype=np.float32)
    edges = np.abs(np.gradient(arr)[0]) + np.abs(np.gradient(arr)[1])
    heat = (edges - edges.min()) / (edges.max() - edges.min() + 1e-8)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.cm as cm

    colored = cm.jet(heat)[:, :, :3]
    colored = (colored * 255).astype("uint8")
    overlay = Image.fromarray(colored).resize(img.size)
    blended = Image.blend(img, overlay, alpha=0.45)

    buf = io.BytesIO()
    blended.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _detection_heatmap(image_path: str, detections: list[dict]) -> str:
    """在原图上按检测框中心叠加高斯热力，反映 YOLO 关注区域。"""
    import numpy as np
    from PIL import Image

    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    heat = np.zeros((h, w), dtype=np.float32)

    yy, xx = np.mgrid[0:h, 0:w]
    for det in detections:
        box = det.get("bbox") or {}
        conf = float(det.get("confidence", 0.5))
        x = float(box.get("x", 0)) * w
        y = float(box.get("y", 0)) * h
        bw = max(float(box.get("width", 0.1)) * w, 8)
        bh = max(float(box.get("height", 0.1)) * h, 8)
        cx = x + bw / 2
        cy = y + bh / 2
        sigma = max(bw, bh) * 0.45
        heat += conf * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma**2))

    if heat.max() > 0:
        heat = heat / heat.max()

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.cm as cm

    colored = (cm.jet(heat)[:, :, :3] * 255).astype(np.uint8)
    overlay = Image.fromarray(colored)
    blended = Image.blend(img, overlay, alpha=0.48)

    buf = io.BytesIO()
    blended.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _pytorch_gradcam(image_path: str) -> str:
    import torch
    import torch.nn.functional as F
    from PIL import Image
    from torchvision import models, transforms

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
    model.eval().to(device)

    target_layer = model.layer4[-1]
    activations = []
    gradients = []

    def fwd_hook(_m, _i, o):
        activations.append(o)

    def bwd_hook(_m, _gi, go):
        gradients.append(go[0])

    h1 = target_layer.register_forward_hook(fwd_hook)
    h2 = target_layer.register_full_backward_hook(bwd_hook)

    preprocess = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    img = Image.open(image_path).convert("RGB")
    orig = img.resize((224, 224))
    tensor = preprocess(img).unsqueeze(0).to(device)
    tensor.requires_grad_(True)

    output = model(tensor)
    score = output[0, output.argmax(dim=1)]
    model.zero_grad()
    score.backward()

    grads = gradients[0][0]
    acts = activations[0][0]
    weights = grads.mean(dim=(1, 2))
    cam = torch.zeros(acts.shape[1:], device=device)
    for i, w in enumerate(weights):
        cam += w * acts[i]
    cam = F.relu(cam)
    cam = cam - cam.min()
    cam = cam / (cam.max() + 1e-8)
    cam_np = cam.detach().cpu().numpy()

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.cm as cm
    import numpy as np

    heatmap = cm.jet(cam_np)[:, :, :3]
    heatmap = (heatmap * 255).astype(np.uint8)
    overlay = Image.fromarray(heatmap).resize(orig.size)
    blended = Image.blend(orig, overlay, alpha=0.5)

    h1.remove()
    h2.remove()

    buf = io.BytesIO()
    blended.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def generate_gradcam(image_path: str, detections: list[dict] | None = None) -> dict:
    # 1) 有检测框 → 病害相关热力图（真实 YOLO 关注区）
    if detections:
        try:
            return {
                "heatmap_base64": _detection_heatmap(image_path, detections),
                "method": "YOLO-Detection-Heatmap",
                "note": f"基于 {len(detections)} 个检测框生成关注区域热力图",
            }
        except Exception:
            pass

    # 2) 尝试跑默认检测再生热力图
    try:
        from predictors import _run_detection_router
        from model_registry import DEFAULT_DETECTION_MODEL

        result = _run_detection_router(image_path, DEFAULT_DETECTION_MODEL, conf=0.2)
        dets = result.get("detections") or []
        if dets:
            return {
                "heatmap_base64": _detection_heatmap(image_path, dets),
                "method": "YOLO-Detection-Heatmap",
                "note": f"基于检测模型 {result.get('model_label', '')} · {len(dets)} 个目标",
            }
    except Exception:
        pass

    # 3) ResNet Grad-CAM / 显著性回退
    try:
        heatmap_b64 = _pytorch_gradcam(image_path)
        method = "PyTorch-ResNet18-GradCAM"
        note = "未检出目标，回退 ImageNet Grad-CAM 通用关注区"
    except Exception:
        heatmap_b64 = _fallback_saliency(image_path)
        method = "OpenCV-Saliency-Fallback"
        note = "未检出目标且 Grad-CAM 不可用，使用边缘显著性回退"

    return {
        "heatmap_base64": heatmap_b64,
        "method": method,
        "note": note,
    }
