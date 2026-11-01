# Restaurant API Tests

基于 Python、requests 和 pytest 的个人接口测试实践。被测系统为 [Restaurant Reservation Platform](https://github.com/Peggeyyy/restaurant-reservation-platform)，应用代码和原有 Java 测试属于原作者。本仓库提供独立的 Python 测试及本机部署辅助配置。

## 当前测试范围

- 餐厅列表与不存在餐厅查询。
- 正常登录、错误密码、密码缺失/空字符串/纯空格、注册。
- 带 Token 查询自身资料，以及未认证访问拦截。
- 创建预约、查询、取消和取消后状态检查；包含已知预约编号时的失败清理。

最近一次学习者全套执行：11 passed in 0.55s。该结果是一次历史记录，不代表每次运行或所有业务规则均已验证。尚未实现 CI、并发专项或完整权限覆盖。

## 目录

```text
tests/                 按业务组织的测试
conftest.py            base_url 与登录 fixture、私有配置加载
requirements.txt       Python 依赖
deploy/                本机隔离部署和基础数据准备脚本
```

## Python 环境与测试配置

在 WSL/Linux 中使用 Python 3.12：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

在项目根目录私有 `.env` 中配置 `TEST_LOGIN_PASSWORD`，值为已注册的本地练习账号 `user@example.com` 的密码。可选 `TEST_BASE_URL`，默认 `http://127.0.0.1:18080`。pytest 收集时由 conftest.py 加载配置，不需要手动 export。`.env` 不应提交。

```bash
pytest -v tests/
pytest -v tests/test_reservations.py
```

## 本机被测环境

现有部署使用相邻目录 `../restaurant-reservation-sut` 中的原项目 Compose 文件。本仓库的覆盖配置使用独立项目名 `restaurant-practice`，API 绑定 `127.0.0.1:18080`，数据库和 Redis 不发布宿主机端口。

部署所需私有 `deploy/.env` 不在仓库内，需要按原项目 Compose 要求另行配置数据库、JWT 和初始化管理员参数；本仓库不是无需配置即可运行的独立应用。

在基础镜像和应用镜像已准备的本机上：

```bash
./deploy/compose.sh up -d --no-build --wait --wait-timeout 180
./deploy/compose.sh ps
```

Swagger：<http://localhost:18080/swagger-ui.html>。`deploy/prepare_data.py` 使用私有管理员配置准备专用餐厅和桌位。当前预约测试依赖本机餐厅1、桌位1（4人，营业09:00–22:00）；其他环境需调整数据，不应假定编号通用。

`deploy/build.sh` 是当前 Windows/WSL 代理环境的构建辅助脚本，默认使用现有代理端口7890；不是通用 CI 配置。Dockerfile 构建跳过原作者 Java 测试，不能据此声称这些测试通过。Compose 将数据库方言显式设为 MySQLDialect。

## 数据与运行限制

注册测试使用动态邮箱，会保留测试用户；预约取消改变状态，不物理删除记录。当前失败清理不涵盖创建结果未知、无法获取编号等所有网络异常。固定不存在编号999的前提也可能随数据变化。请仅在独立测试环境执行，不清空其他项目的数据卷。

自动生成的 evidence/、虚拟环境、缓存和私有凭据不提交。教学计划、进度和Agent交接文档仅在本机维护。
