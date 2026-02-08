---
title: 修复 ThinkBook 14+ 扬声器问题
date: 2026-02-08
---

这个问题其实已经困扰我很久了，起初是重装了 Arch Linux 后，某一次电脑睡眠唤醒后，扬声器右边比左边声音大了很多，使用 pavucontrol 强制对齐两个声道的声音大小后就可以暂时恢复，但是后来这个方法也不行了，尤其是换了 linux-zen 内核后完全不起作用 ...

想了很多办法都没有解决，今天突发奇想，做了一个 Linux-Mint 的 LiveCD，进去之后发现居然没有问题 ... 很纳闷，于是似乎找到了解决办法。

```bash
sudo dmesg | grep -Ei "snd|cs35|sof"
```

显示我的声卡被识别为 ALC257，并且正在使用 SOF 驱动 (sof-audio-pci-intel-mtl)，这是 Intel Meteor Lake(Core Ultra) 的标准新架构。Linux Mint 22.3 基于 Ubuntu 24.04 LTS（内核较旧或策略保守），它很可能默认使用的是 Legacy HDA 驱动模式，而不是新的 SOF 架构。而在 Arch Linux 上，由于内核非常新，它默认启用了 SOF 架构。虽然 SOF 更先进，但在某些 ThinkBook/Legion 机型上，它对 ALC257 的引脚映射不正确，导致低音单元和高音单元分配错误，从而出现一边声音大，一边声音小的现象，需要尝试修改驱动加载策略，让 Arch 模仿 Mint 的行为，或者修正 SOF 的映射。

考虑到我启用了 UKI，虽然可以通过修改内核启动参数来解决，但这通常涉及到重新签名或调整构建配置，比较繁琐。更简单是利用 modprobe 配置文件。只需要在 /etc/modprobe.d/ 下创建一个配置文件，指定内核模块的加载参数，并重新构建 UKI（将其打包进 initramfs），即可让系统在启动加载驱动时强制使用旧版 HDA 模式。

```bash
echo "options snd_intel_dspcfg dsp_driver=1" | sudo tee /etc/modprobe.d/fix-audio.conf
sudo mkinitcpio -P
sudo reboot
```