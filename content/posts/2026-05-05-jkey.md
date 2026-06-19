---
title: Python library for password management and TOTP verification
date: 2026-05-04
---

之前一直用谷歌验证器和 1Password，但总感觉太重了，而且总会依赖别人的服务，后来想了想，我的需求其实很简单，最主要就是两步验证 2FA，没必要搞那么复杂，之前使用 Python 简单写了几个脚本来实现，最近用上了 agent，想着重构一下做成 pip 包更方便。

所以就写了 jkey，一个纯 Python 的密码管理工具，就用我的名字开头字母命名吧，简短一些。AES-256-CBC 加密，所有数据存在本地 `~/.config/jkey/`，除了扫二维码需要 opencv，其他全是纯 Python，零外部依赖。

项目地址：https://github.com/imjiaoyuan/jkey

直接使用 uv 安装：

```bash
uv tool install jkey
```

首先需要初始化并设置主密码：

```bash
jkey pv init
```

## 2FA 模块

管理 TOTP 两步验证账号。标准 RFC 6238 实现，和谷歌验证器完全兼容，迁移过来的时候直接扫原来的二维码图片就行。

查看账号和当前验证码：

```bash
# 列出所有账号
jkey 2fa ls

# 关键词过滤
jkey 2fa ls github

# 支持大小写不敏感匹配
jkey 2fa ls GMAIL
```

从二维码图片导入账号：

```bash
jkey 2fa add ./github.jpg
```

底层调用 opencv 的 QRCodeDetector 识别二维码，会自动解析 `otpauth://` URI 格式。同时会把原始二维码图片加密备份到 `~/.config/jkey/qr/` 目录下。太大的图片会自动缩放到 1000 像素以内再识别。

删除账号，会同步清理关联的恢复码和二维码备份：

```bash
jkey 2fa rm user@example.com
```

## RC 模块

很多网站的 2FA 验证都会有恢复码作为 2FA 验证失效时的备用验证方案，通常是 txt 文件，所以也需要这个模块。导入时会自动将文件内容解析为恢复码列表，以文件名作为标识。

从文件导入恢复码：

```bash
jkey rc add ./github-recovery.txt
```

列出已导入的恢复码：

```bash
jkey rc ls

# 按账号过滤
jkey rc ls github
```

删除某个账号的恢复码：

```bash
jkey rc rm github
```

## PM 模块

密码管理，包括随机密码生成和密码存储。这个功能其实只是为了补全作为一个密码管理软件所必须的功能吧，可能没多少人会用到，我的密码也都是存在谷歌账号的，手机和 chrome 同步的。

生成随机密码使用 Python 的 `secrets` 模块（CSPRNG）：

```bash
# 默认 16 位，包含大小写字母、数字和符号
jkey pm get

# 生成 32 位密码
jkey pm get -L 32

# 只要字母和数字
jkey pm get -L 20 --no-symbols

# 只要小写字母和数字
jkey pm get -L 20 --no-upper --no-symbols
```

每个字符集至少保证一个字符，所以不会出现生成了 32 位密码结果全是小写字母的情况。

存储和查看密码：

```bash
# 存储密码，交互式输入
jkey pm add github

# 列出所有存储的密码
jkey pm ls

# 按关键词过滤
jkey pm ls github

# 删除密码
jkey pm rm github
```

密码以明文形式打印到终端，设计上倾向于简单直接，既然你问密码就是要用，那就不搞掩码这种多余的操作了。

## PV 模块

jkey 将所有数据存放在保险库中，开始使用 jkey 的时候需要初始化创建一个保险库并且设置主密码：

```bash
jkey pv init
```

会要求输入并确认主密码，然后创建加密数据文件。主密码也可以通过环境变量传入，适合在脚本里用：

```bash
export JKEY_PASS=your-master-password
jkey pv init
```

加解锁操作：

```bash
# 解锁保险库
jkey pv unlock

# 锁定保险库
jkey pv lock
```

解锁后的密码会缓存在 `.session` 文件里（权限 600），5 分钟内跨进程不用重复输入密码，和 sudo 的一样。缓存文件是明文存的，如果你介意这个可以删掉，每次手动解锁就行。

修改主密码：

```bash
jkey pv set-pw
```

用主密码加密文件：

```bash
# 加密文件，输出为原文件名 + .jkey
jkey pv encrypt secret.pdf

# 指定输出路径
jkey pv encrypt secret.pdf -o backup.pdf.jkey
```

解密`.jkey`文件：

```bash
jkey pv decrypt secret.pdf.jkey -o secret.pdf
```

底层加密用的是 AES-256-CBC + HMAC-SHA256，文件会先 base64 编码再加密，适合各种二进制文件。

数据导出，export 命令需要二次确认主密码：

```bash
# 导出 2FA 密钥为 JSON
jkey pv export totp -o totp.json

# 导出密码为 CSV
jkey pv export passwords -o passwords.csv

# 导出恢复码为文本文件
jkey pv export recovery -o recovery.txt

# 导出二维码图片到目录
jkey pv export qr -o ./qr_images

# 导出全部数据
jkey pv export all -o ./backup
```

如果不指定 `-o`，TOTP 和密码数据会直接打印到终端。

## 目录结构

数据文件统一放在 `~/.config/jkey/`，每种数据类型各一个文件，独立加密：

```
~/.config/jkey/
├── .session          # 会话缓存（5 分钟超时）
├── totp.jkey         # 加密的 TOTP secrets
├── passwords.jkey    # 加密的密码
├── recovery.jkey     # 加密的恢复码
└── qr/               # 加密的二维码图片
    └── <account>.jkey
```

加密用的是 AES-256-CBC + HMAC-SHA256。v3 格式把加密密钥和认证密钥分开了，用 PBKDF2-HMAC-SHA256 派生，迭代 60 万次。AES 是我自己用纯 Python 手写的，S 盒、密钥扩展、列混合全部手动实现，没调 OpenSSL。性能比不上 C 实现，但密码管理这种低频操作完全够用。

## 实现细节

这个项目有个小坑，因为我希望命令尽量短，这样用起来更方便，所以核心的 2FA 模块名以数字开头。项目里有个 `2fa/` 目录，Python 的 import 语法不允许 `from jkey.2fa.rm import remove_account`，因为 `2fa` 以数字开头，不是合法的标识符。解决方案是用 `importlib.import_module('jkey.2fa.rm')` 动态导入。

还有就是密码明文输出的设计取舍。一开始想过加 `--mask` 参数来掩码显示，但后来觉得这和密码管理器的使用场景不符，你查密码就是为了复制粘贴，掩码了还要多操作一步。所以就保持简单了。

## 不足

纯 Python AES 速度慢是硬伤。加解密大文件的时候能感觉到明显延迟，所以只适合小文件。如果你需要加密几百 MB 的文件，用 openssl 命令行更靠谱。

另外 opencv 依赖虽然只有一个，但 opencv-python-headless 体积不小（大概 30MB），就为了扫个二维码。以后可以考虑用 `pyzbar` 或者纯 Python 的二维码识别方案替换掉它。

有很多场景的并没有测试，我仅仅在 ArchLinux 上进行了测试，Windows 还没有兼容，后续会补上，希望有用的朋友多提提建议。
