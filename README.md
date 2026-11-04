# 餐厅预约接口测试

这个仓库放的是我为 [Restaurant Reservation Platform](https://github.com/Peggeyyy/restaurant-reservation-platform) 编写的接口测试。测试用 Python、requests 和 pytest，应用服务使用原项目的 Spring Boot、MySQL 和 Redis。

我先测了登录、客户资料和预约的创建、查询、取消，再补上人数与营业时间边界、跨客户访问、状态迁移和幂等性。并发测试发现同一桌位同时段可能创建两笔预约，问题已复现，编号为 BUG-001。

## 怎么运行

准备 Python 3.12 和 Docker Compose。测试仓库与被测源码目录并排放置：

```text
restaurant-api-tests/
restaurant-reservation-sut/
```

被测源码使用 `e0ebb51b3c53118bf73e4cd044372edc5eb01c95`。在测试仓库根目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python deploy/run_ci.py
```

脚本在 `127.0.0.1:28080` 启动一套临时服务，准备客户、餐厅和桌位，跑完后清理这次运行的容器及数据卷。报告在 `evidence/ci-junit.xml`，执行范围在 `evidence/ci-scope.txt`。本机如果需要代理下载构建依赖，可以用 `BUILD_PROXY_HOST` 和 `BUILD_PROXY_PORT` 指定已有代理。

## 本机服务怎么启动

[原项目的启动说明](https://github.com/Peggeyyy/restaurant-reservation-platform/blob/e0ebb51b3c53118bf73e4cd044372edc5eb01c95/README.md)使用 `docker compose up --build`。这里沿用它的 `docker-compose.yml`，在测试时再叠加 `deploy/compose.test.yml`。主要区别是给测试单独的 Compose 项目和数据卷，把 API 改到 `127.0.0.1:18080`，以及取消 MySQL 和 Redis 的宿主机端口映射。覆盖文件也明确指定 MySQL 方言，并使用本仓库的构建文件。

已有私有 `deploy/.env` 和构建镜像的本机可以这样启动日常测试环境：

```bash
./deploy/compose.sh up -d --no-build --wait --wait-timeout 180
```

[打开本机 Swagger](http://localhost:18080/swagger-ui.html)。测试读取项目根目录 `.env` 的 `TEST_LOGIN_PASSWORD`，使用本机练习账号 `user@example.com`。数据初始化入口是 `deploy/prepare_data.py`，用管理员账号准备餐厅和桌位。当前用例依赖测试数据的编号，换环境时建议使用上面的临时环境脚本。

## 测试结果

[一次 GitHub Actions 回归](https://github.com/AmazingYe-oss/restaurant-api-tests/actions/runs/41822604263)中，28 项通过。回归显式排除了 BUG-001 对应的并发用例，单独复现可以运行：

```bash
pytest -v tests/test_reservations.py -k concurrent_reservations
```

这个命令会尝试创建预约，请在测试环境执行。预约清理通过取消操作完成，数据库仍保留记录。注册用例也会留下测试客户。接口规则和响应字段见 [预约接口约定](RESERVATION_SPEC.md)。
