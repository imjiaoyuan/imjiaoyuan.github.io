---
title: 在曙光服务器上公共部署 Claude Code
date: 2026-07-14
---

之前写过一篇[在生信工作中使用 agent](/5xbok/)，里面用的是 npm 全局安装 Claude Code。但现在 Anthropic 废弃了 npm 安装方式，现在只能下载官方二进制包来装。正好最近要在曙光服务器上部署 Claude Code，这台机器跑的是 CentOS 7，glibc 老得不行，折腾了一下才搞定。

## 环境问题

曙光服务器的环境如下：

```
NAME="CentOS Linux"
VERSION="7 (Core)"
ID="centos"
ID_LIKE="rhel fedora"
VERSION_ID="7"
```

Claude Code 自带一些内置 hook，这些 hook 是 Node.js 脚本，所以必须要有 Node.js 运行环境。但 CentOS 7 没有预装 Node.js，从官网下最新版的 tar.xz 解压直接跑会报 glibc 符号找不到的错误。

解决方法是用 conda 装 Node.js，conda 环境自带一套兼容的 so 库，不受系统 glibc 版本限制。然后把 node、npm、npx 软链接到公共 bin 目录，各用户加一下环境变量就能用。

## GitHub 代理

国内服务器访问 GitHub 很慢，下载 Claude Code 的 release 包基本不可用。在 Cloudflare Workers 上部署下面这段脚本，绑定域名 `github.jiaoyuan.org`，给服务器做 GitHub 加速。

```ts
interface Config {
  jsdelivr: boolean;
  whiteList: string[];
  prefix: string;
}

type RouteAction =
  | { type: 'proxy'; url: string }
  | { type: 'redirect'; url: string; status: number };

const PREFIX = '/';

const config: Config = {
  jsdelivr: false,
  whiteList: [],
  prefix: PREFIX,
};

const exp1 = /^(?:https?:\/\/)?github\.com\/.+?\/.+?\/(?:releases|archive)\/.*$/i;
const exp2 = /^(?:https?:\/\/)?github\.com\/.+?\/.+?\/(?:blob|raw)\/.*$/i;
const exp3 = /^(?:https?:\/\/)?github\.com\/.+?\/.+?\/(?:info|git-).*$/i;
const exp4 = /^(?:https?:\/\/)?raw\.(?:githubusercontent|github)\.com\/.+?\/.+?\/.+?\/.+$/i;
const exp5 = /^(?:https?:\/\/)?gist\.(?:githubusercontent|github)\.com\/.+?\/.+?\/.+$/i;
const exp6 = /^(?:https?:\/\/)?github\.com\/.+?\/.+?\/tags.*$/i;

const ALL_PATTERNS = [exp1, exp2, exp3, exp4, exp5, exp6] as const;

function checkUrl(u: string): boolean {
  return ALL_PATTERNS.some(exp => u.search(exp) === 0);
}

function route(path: string): RouteAction | null {
  if ([exp1, exp5, exp6, exp3].some(exp => path.search(exp) === 0)) {
    return { type: 'proxy', url: path };
  }
  if (path.search(exp2) === 0) {
    if (config.jsdelivr) {
      const cdn = path
        .replace('/blob/', '@')
        .replace(/^(?:https?:\/\/)?github\.com/, 'https://cdn.jsdelivr.net/gh');
      return { type: 'redirect', url: cdn, status: 302 };
    }
    return { type: 'proxy', url: path.replace('/blob/', '/raw/') };
  }
  if (path.search(exp4) === 0) {
    if (config.jsdelivr) {
      const cdn = path
        .replace(/(?<=com\/.+?\/.+?)\/(.+?\/)/, '@$1')
        .replace(/^(?:https?:\/\/)?raw\.(?:githubusercontent|github)\.com/, 'https://cdn.jsdelivr.net/gh');
      return { type: 'redirect', url: cdn, status: 302 };
    }
    return { type: 'proxy', url: path };
  }
  return null;
}

const PREFLIGHT_INIT: ResponseInit = {
  status: 204,
  headers: {
    'access-control-allow-origin': '*',
    'access-control-allow-methods': 'GET,POST,PUT,PATCH,TRACE,DELETE,HEAD,OPTIONS',
    'access-control-max-age': '1728000',
  },
};

function handlePreflight(request: Request): Response | null {
  if (request.method === 'OPTIONS' && request.headers.has('access-control-request-headers')) {
    return new Response(null, PREFLIGHT_INIT);
  }
  return null;
}

function isWhitelisted(url: string): boolean {
  if (config.whiteList.length === 0) return true;
  return config.whiteList.some(item => url.includes(item));
}

function safeParseUrl(urlStr: string): URL | null {
  try { return new URL(urlStr); } catch { return null; }
}

async function proxyRequest(
  request: Request,
  targetUrl: string,
  maxRedirects = 10,
): Promise<Response> {
  if (!isWhitelisted(targetUrl)) {
    return new Response('blocked', { status: 403 });
  }
  let urlStr = targetUrl;
  if (!/^https?:\/\//.test(urlStr)) urlStr = 'https://' + urlStr;
  const urlObj = safeParseUrl(urlStr);
  if (!urlObj) return new Response('Invalid URL', { status: 400 });
  if (maxRedirects <= 0) return new Response('Too many redirects', { status: 502 });

  const upstream = await fetch(urlObj.href, {
    method: request.method,
    headers: new Headers(request.headers),
    redirect: 'manual',
    body: request.body,
  });

  const resHeaders = new Headers(upstream.headers);
  const location = resHeaders.get('location');
  if (location) {
    if (checkUrl(location)) {
      resHeaders.set('location', config.prefix + location);
    } else {
      return proxyRequest(request, location, maxRedirects - 1);
    }
  }
  resHeaders.set('access-control-expose-headers', '*');
  resHeaders.set('access-control-allow-origin', '*');
  resHeaders.delete('content-security-policy');
  resHeaders.delete('content-security-policy-report-only');
  resHeaders.delete('clear-site-data');
  return new Response(upstream.body, { status: upstream.status, headers: resHeaders });
}

const INDEX_HTML = `<!DOCTYPE html>
<html lang="zh-Hans">
<style>
    html,body{width:100%;margin:0}html{height:100%}body{min-height:100%;padding:20px;box-sizing:border-box}p{word-break:break-all}
    @media(max-width:500px){h1{margin-top:80px}}
    .flex{display:flex;flex-direction:column;justify-content:center;align-items:center}
    .block{display:block;position:relative}
    .url{font-size:18px;padding:10px 10px 10px 5px;position:relative;width:300px;border:none;border-bottom:1px solid #bfbfbf}
    input:focus{outline:none}
    .bar{content:'';height:2px;width:100%;bottom:0;position:absolute;background:#00bfb3;transition:0.2s ease transform;transform:scaleX(0)}
    .url:focus~.bar{transform:scaleX(1)}
    .btn{line-height:38px;background-color:#00bfb3;color:#fff;white-space:nowrap;text-align:center;font-size:14px;border:none;border-radius:2px;cursor:pointer;padding:5px;width:160px;margin:30px 0}
    .tips,.example{color:#7b7b7b;position:relative;align-self:flex-start;margin-left:7.5em}
    .tips>p:first-child::before{position:absolute;left:-3em;content:'PS：';color:#7b7b7b}
    .example>p:first-child::before{position:absolute;left:-7.5em;content:'合法输入示例：';color:#7b7b7b}
</style>
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <script>
        function toSubmit(e){e.preventDefault();window.open(location.href.substr(0,location.href.lastIndexOf('/')+1)+document.getElementsByName('q')[0].value);return false}
        function copyLink(){const u=location.origin+'/'+document.getElementsByName('q')[0].value;navigator.clipboard.writeText(u).then(()=>{const b=document.getElementById('copy-btn');b.textContent='已复制';setTimeout(()=>{b.textContent='复制链接'},1500)}).catch(()=>{const b=document.getElementById('copy-btn');b.textContent='复制失败';setTimeout(()=>{b.textContent='复制链接'},1500)})}
    </script>
    <title>GitHub 文件加速</title>
</head>
<body class="flex">
<a style="position:absolute;top:0;right:0;color:#3294ea;text-decoration:none;padding:8px 12px;font-size:14px" href="https://github.com/imjiaoyuan/proxyfox">Fork me on GitHub</a>
<h1 style="margin-bottom:50px">GitHub 文件加速</h1>
<form action="./" method="get" style="padding-bottom:40px" target="_blank" class="flex" onsubmit="toSubmit(event)">
    <label class="block" style="width:fit-content">
        <input class="block url" name="q" type="text" placeholder="键入Github文件链接"
               pattern="^((https|http):\\/\\/)?(github\\.com\\/.+?\\/.+?\\/(?:releases|archive|blob|raw|suites)|((?:raw|gist)\\.(?:githubusercontent|github)\\.com))\\/.+$" required>
        <div class="bar"></div>
    </label>
    <div style="display:flex;gap:12px">
        <input class="block btn" type="submit" value="下载">
        <button class="block btn" type="button" id="copy-btn" onclick="copyLink()" style="background-color:#526069">复制链接</button>
    </div>
    <div class="tips"><p>GitHub 文件链接带不带协议头都可以，支持 release、archive 以及文件。更多用法、clone 加速请参考 <a href="https://github.com/imjiaoyuan/proxyfox">项目文档</a>。</p><p>注意，不支持项目文件夹</p></div>
    <div class="example"><p>分支源码：https://github.com/user/project/archive/master.zip</p><p>release源码：https://github.com/user/project/archive/v0.1.0.tar.gz</p><p>release文件：https://github.com/user/project/releases/download/v0.1.0/example.zip</p><p>分支文件：https://github.com/user/project/blob/master/filename</p></div>
</form>
<p style="position:sticky;top:calc(100% - 2.5em)">项目基于 Cloudflare Workers，开源于 GitHub <a style="color:#3294ea" href="https://github.com/imjiaoyuan/proxyfox">imjiaoyuan/proxyfox</a></p>
</body>
</html>`;

const FAVICON_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="4" fill="#00bfb3"/><text x="16" y="22" text-anchor="middle" font-size="20" font-family="sans-serif" fill="#fff">→</text></svg>`;

function handleStaticFile(pathname: string): Response | null {
  if (pathname === '/' || pathname === '') {
    return new Response(INDEX_HTML, { headers: { 'content-type': 'text/html; charset=utf-8' } });
  }
  if (pathname === '/favicon.ico') {
    return new Response(FAVICON_SVG, { headers: { 'content-type': 'image/svg+xml' } });
  }
  return null;
}

async function handleRequest(request: Request): Promise<Response> {
  const urlObj = new URL(request.url);

  const q = urlObj.searchParams.get('q');
  if (q) return Response.redirect(\`https://\${urlObj.host}\${PREFIX}\${q}\`, 301);

  const preflight = handlePreflight(request);
  if (preflight) return preflight;

  const staticResp = handleStaticFile(urlObj.pathname);
  if (staticResp) return staticResp;

  const path = urlObj.href
    .slice(urlObj.origin.length + PREFIX.length)
    .replace(/^https?:\/+/, 'https://');

  const action = route(path);
  if (!action) return new Response('Not Found', { status: 404 });

  switch (action.type) {
    case 'proxy': return proxyRequest(request, action.url);
    case 'redirect': return Response.redirect(action.url, action.status);
  }
}

export default { fetch: handleRequest };
```

这个 Workers 脚本支持代理 GitHub release、archive、raw 文件以及 gist，部署到 Cloudflare 后绑个域名就能用。

## 下载 Claude Code 二进制

下面这个脚本会自动获取最新版本、走代理下载二进制、校验 checksum、安装到公共目录，并打包成离线压缩包方便分发：

```bash
#!/bin/bash
set -e

rm -rf ./claude-code-offline
mkdir -p ./claude-code-offline

VERSION=$(curl -s https://api.github.com/repos/anthropics/claude-code/releases/latest | grep -m1 '"tag_name"' | sed -E 's/.*"tag_name": "([^"]+)".*/\1/')
echo "version: $VERSION"
echo $VERSION > ./claude-code-offline/latest

TMP_TAR=$(mktemp)
curl -fsSL -o "$TMP_TAR" "https://github.jiaoyuan.org/https://github.com/anthropics/claude-code/releases/download/${VERSION}/claude-linux-x64.tar.gz"

TMP_DIR=$(mktemp -d)
tar -xzf "$TMP_TAR" -C "$TMP_DIR" 2>/dev/null
BIN=$(find "$TMP_DIR" -type f -name claude | head -1)
mkdir -p "./claude-code-offline/${VERSION}/linux-x64"
cp "$BIN" "./claude-code-offline/${VERSION}/linux-x64/claude"
chmod +x "./claude-code-offline/${VERSION}/linux-x64/claude"
sha256sum "./claude-code-offline/${VERSION}/linux-x64/claude" | awk '{print $1}' > "./claude-code-offline/${VERSION}/linux-x64/checksum"

rm -f "$TMP_TAR"
rm -rf "$TMP_DIR"

cat > ./claude-code-offline/install.sh << 'EOF'
#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
version=$(cat "$SCRIPT_DIR/latest")
binary="$SCRIPT_DIR/$version/linux-x64/claude"
checksum_file="$SCRIPT_DIR/$version/linux-x64/checksum"
if [ -f "$checksum_file" ]; then
    expected=$(cat "$checksum_file")
    actual=$(sha256sum "$binary" | cut -d' ' -f1)
    if [ "$actual" != "$expected" ]; then
        echo "checksum mismatch" >&2
        exit 1
    fi
fi
chmod +x "$binary"
INSTALL_DIR="${1:-/public/share/ac4w0a7em6/bin}"
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR" || { echo "cannot create $INSTALL_DIR" >&2; exit 1; }
fi
if [ ! -w "$INSTALL_DIR" ]; then
    echo "no write permission to $INSTALL_DIR" >&2
    exit 1
fi
cp "$binary" "$INSTALL_DIR/claude"
chmod 755 "$INSTALL_DIR/claude"
echo "installed to $INSTALL_DIR/claude"
EOF

chmod +x ./claude-code-offline/install.sh

tar_name="claude-code-offline-${VERSION}.tar.gz"
tar -czf "$tar_name" -C ./claude-code-offline .

bash ./claude-code-offline/install.sh

rm -rf ./claude-code-offline

echo "done: $tar_name"
```

脚本做了几件事：从 GitHub API 获取最新版本号，走 `github.jiaoyuan.org` 代理下载 tar.gz，解压提取 claude 二进制并计算 sha256，校验后安装到公共目录，最后打包成离线压缩包方便分发。

## 用 conda 装 Node.js 并软链接

Claude Code 内置了一些 hook（比如检查更新、上报使用数据等），这些 hook 是用 Node.js 写的，所以光有 claude 二进制还不够，必须装 Node.js。但 CentOS 7 的 glibc 太老，从 Node.js 官网下最新版的 tar.xz 解压直接跑会报类似这样的错：

```
/lib64/libc.so.6: version `GLIBC_2.18' not found
```

用 conda 安装可以绕过这个问题：conda 环境自带了一套经过兼容处理的 so 库，不依赖系统 glibc：

```bash
conda create -p /public/share/ac4w0a7em6/claude
conda install conda-forge::nodejs
```

装好之后，Node.js 在 conda 环境的 `bin/` 下。为了方便所有用户使用，把 node、npm、npx 软链接到公共 bin 目录：

```bash
cd /public/share/ac4w0a7em6/bin
ln -s /public/share/ac4w0a7em6/claude/bin/node node
ln -s /public/share/ac4w0a7em6/claude/bin/npm npm
ln -s /public/share/ac4w0a7em6/claude/bin/npx npx
```

最终公共 bin 目录的结构：

```
/public/share/ac4w0a7em6/bin/
├── claude           # Claude Code 二进制
├── claude-clean.sh  # Node 进程清理脚本
├── node -> /public/share/ac4w0a7em6/claude/bin/node
├── npm  -> /public/share/ac4w0a7em6/claude/bin/npm
└── npx  -> /public/share/ac4w0a7em6/claude/bin/npx
```

各用户只需要在 `~/.bashrc` 中加上：

```bash
export PATH="/public/share/ac4w0a7em6/bin:$PATH"
export NODE_OPTIONS="--max-old-space-size=8192"
```

`NODE_OPTIONS` 限制 Node.js 堆内存上限为 8GB，防止 Claude Code 某些操作申请过多内存。

## 清理僵尸 Node 进程

Claude Code 运行时会启动很多 Node 子进程，尤其是 subagent 并发的时候。如果用户开了好几个 Claude Code 实例，Node 进程数会迅速膨胀。更麻烦的是，大量进程申请的虚拟内存总和可能触发系统 OOM killer，导致 claude 进程被直接杀掉。

所以写了个清理脚本 `claude-clean.sh`，当 Node 进程数超过阈值时自动 kill：

```bash
#!/bin/bash
MAX_NODE_PROCESSES=50
count=$(pgrep -u $USER -c -f "node.*claude" 2>/dev/null)
[ -z "$count" ] && count=0
if [ $count -gt $MAX_NODE_PROCESSES ]; then
    echo "$(date): killing $count node processes for claude"
    pkill -9 -u $USER -f "node.*claude"
else
    echo "$(date): claude-related node processes: $count, below threshold $MAX_NODE_PROCESSES, no action needed"
fi
```

阈值设为 50，正常使用一般不会超过，超过了说明有进程泄漏或者僵尸进程积压，直接清掉。配合 `NODE_OPTIONS` 的内存限制，基本不会再遇到 OOM 问题。

可以加到 crontab 里每半小时跑一次：

```bash
*/30 * * * * /public/share/ac4w0a7em6/bin/claude-clean.sh >> ~/claude-clean.log 2>&1
```

## 使用

用户配好 `PATH` 和环境变量后，直接 `claude` 就能启动。API key 和模型配置参考[之前的文章](/5xbok/)，用 `ccapi` 函数切换不同来源的 key 比较方便。

这套方案目前跑在曙光服务器上，几个同学同时用也没出什么问题。核心思路就是：把二进制和 Node.js 都放到公共目录，用 conda 解决 glibc 兼容性，软链接统一入口，环境变量控制资源，定时脚本防泄漏。老旧服务器上多人共享 AI agent 也不是不行，多绕几步路而已。
