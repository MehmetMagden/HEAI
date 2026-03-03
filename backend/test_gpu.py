# test_gpu.py
import torch

if torch.cuda.is_available():
    print(f"CUDA bulundu! Kullanılabilir GPU: {torch.cuda.get_device_name(0)}")
    print(f"PyTorch versiyonu: {torch.__version__}")
    print(f"CUDA versiyonu: {torch.version.cuda}")
else:
    print("UYARI: CUDA kullanılamıyor. Lütfen PyTorch kurulumunuzu ve NVIDIA sürücülerinizi kontrol edin.")