---
title: Bionanoaccess 安装
date: 2024-09-02
---

之前帮一位老师安装了 bionano，过程还是比较繁琐的，根据官网的安装文档进行了一些补充。

<!--more-->

创建新用户：
```bash
useradd -m -G wheel -s /bin/bash bionano
passwd bionano
```
安装依赖：
```bash
sudo yum install –y perl
sudo yum install -y java-1.8.0-openjdk
sudo yum install -y python3
curl --silent --location https://rpm.nodesource.com/setup_12.x | sudo bash -
sudo yum install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-7-x86_64/pgdg-redhat-repo-latest.noarch.rpm
sudo yum install -y postgresql12 postgresql-12-server postgresql12-contrib
sudo /usr/pgsql-12/bin/postgresql-12-setup initdb
sudo cp /var/lib/pgsql/12/data/pg_hba.conf /var/lib/pgsql/12/data/pg_hba.conf.orig
sudo bash -c 'echo "local all all peer">/var/lib/pgsql/12/data/pg_hba.conf'
sudo bash -c 'echo "host all all 127.0.0.1/32 md5" >>/var/lib/pgsql/12/data/pg_hba.conf'
sudo bash -c 'echo "host all all ::1/128 md5" >>/var/lib/pgsql/12/data/pg_hba.conf'

sudo systemctl start postgresql-12
sudo systemctl enable postgresql-12
sudo -i -u bionano psql -U bionano -d bionano -c "alter user bionano with password '123456';"
sudo systemctl restart postgresql-12
sudo yum install npm
sudo npm config set registry https://registry.npmmirror.com/
```
服务器开放 3005、3006 端口。

这里要手动生成一个 SSL 证书，以便于后面访问 web 客户端，web 客户端的静态资源都是指向 https 的，所以使用 http 会出现白屏什么都没加载的情况。

```bash
openssl genpkey -algorithm RSA -out key.pem
```
随后将两个 pem 移动到`/home/bionano/access/web/Server`。

```bash
sudo iptables -A INPUT -p tcp --dport 3005 -j ACCEPT
cd /home/bionano/access/web/Server
node --max-old-space-size=32768 server default https
```
访问 ip:3006 如 https://47.115.149.127:3006/