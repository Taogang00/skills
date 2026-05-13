---
name: java-dev-guide
description: JavaWeb开发规范与代码优化指导skill。当用户涉及Java代码编写、审查、优化、重构，Spring Boot项目开发，RESTful API设计，命名规范检查，代码质量提升，阿里巴巴Java开发手册规范落地等任务时，必须使用此skill。触发场景包括：写Java类/方法/变量、设计REST接口、单元测试、审查代码规范、优化Spring Boot项目、处理异常、设计数据库字段命名、多线程编程、日志记录等一切Java后端开发相关任务。
---

# JavaWeb 开发规范与代码优化指导

本 skill 覆盖以下核心规范体系，涉及具体子主题时，参考 `references/` 对应文件：

| 参考文件                               | 内容                           |
|------------------------------------|------------------------------|
| `references/base.md`               | 必须遵守的约定规范                    |
| `references/naming.md`             | 命名规范（类、方法、变量、常量、包、DB字段等）     |
| `references/springboot-restful.md` | Spring Boot RESTful API 设计规范 |
| `references/code-style.md`         | 代码格式、注释、OOP规约、集合使用           |
| `references/exception-log.md`      | 异常处理与日志规范                    |
| `references/concurrency.md`        | 并发与线程池规范                     |
| `references/optimization.md`       | 代码优化与性能调优指导                  |

---

## 使用流程

1. **判断任务类型**：命名 → `naming.md`；REST接口 → `springboot-restful.md`；代码审查/优化 → 按需读取多个文件
2. **读取对应参考文件**，严格按规范给出建议或生成代码
3. **输出格式**：
    - 代码问题：指出违规点 + 引用规则编号 + 给出修正代码
    - 代码生成：直接输出符合规范的完整代码，关键规范用注释标注
    - 优化建议：分级列出（P0 必须修改 / P1 建议修改 / P2 可以优化）

---

## 快速规范速查（无需读文件的高频规则）

### 1、强制命名规则

- 类名：`UpperCamelCase`（DO/BO/DTO/VO/AO/PO/UID 等除外保持全大写），枚举类禁止太简单抽象，如EnumState.class
- 方法名/变量名：`lowerCamelCase`
- 常量：`UPPER_SNAKE_CASE`，必须用 `static final`
- 包名：全小写，点分隔，`com.guanwei.{业务}.{模块}`
- 布尔变量：**禁止**以 `is` 开头（POJO中会导致序列化问题），用 `flag`/`enabled`/`valid` 等
- 抽象类：以 `Abstract`/`Base` 开头；异常类：以 `Exception` 结尾；测试类：以 `Test` 结尾

### 2、Spring Boot RESTful 核心规则

- URL 用**名词复数**，小写连字符：`/api/v1/user-orders`
- HTTP动词语义：`GET`查询 / `POST`新增 / 禁止使用PUT、PATCH、DELETE等请求方法
- 统一响应体：`{ "sussess": true, "message": "success", "data": {} }`

### 3、代码质量红线

- 集合返回值**不允许**返回 `null`，返回空集合
- 所有资源（流、连接）必须在 `finally` 或 try-with-resources 中关闭
- 线程必须命名，禁止直接 `new Thread()`，使用线程池
- 日志使用占位符 `log.info("user:{}", userId)`，禁止字符串拼接
