# 知识库模块测试文档

## 概述

知识库模块提供了完整的自动化测试套件，确保数据访问层和API层的稳定性和正确性。测试使用 `unittest` 框架，在隔离的临时数据库环境中运行，不会影响生产数据。

## 测试文件

### tests/test_knowledge_module.py

主要测试文件，包含两个测试类：

1. **TestKnowledgeRepository** - 测试知识库存储层 (`knowledge_repository.py`)
2. **TestKnowledgeAPI** - 测试知识库API端点 (`knowledge_api.py`)

## 运行测试

### 运行所有知识库测试

```bash
cd wp
python -m unittest tests.test_knowledge_module -v
```

### 运行特定测试类

```bash
# 只测试存储层
python -m unittest tests.test_knowledge_module.TestKnowledgeRepository -v

# 只测试API层
python -m unittest tests.test_knowledge_module.TestKnowledgeAPI -v
```

### 运行特定测试方法

```bash
python -m unittest tests.test_knowledge_module.TestKnowledgeRepository.test_tag_derivation -v
```

### 发现并运行所有测试

```bash
python -m unittest discover tests -v
```

## 测试覆盖范围

### 存储层测试 (TestKnowledgeRepository)

#### 1. 标签提取 (test_tag_derivation)
- 测试从URL路径提取标签的各种情况
- 验证正常URL、空URL、非法URL的处理
- 确保默认返回"未分类"

#### 2. 基础列表功能 (test_list_entries_basic)
- 验证返回数据结构
- 检查总数计算
- 确认条目数量正确

#### 3. 分页功能 (test_list_entries_pagination)
- 测试不同页码返回不同数据
- 验证 `has_more` 标志
- 确认偏移量正确应用

#### 4. 全文搜索 (test_list_entries_search)
- 测试标题搜索
- 测试文章ID搜索
- 测试链接URL搜索
- 验证模糊匹配

#### 5. 状态过滤 (test_list_entries_status_filter)
- 测试 pending/completed/transferred/failed 各状态
- 验证过滤结果准确性

#### 6. 标签过滤 (test_list_entries_tag_filter)
- 测试按标签筛选
- 验证动态标签提取

#### 7. 日期范围过滤 (test_list_entries_date_filter)
- 测试起始日期和结束日期
- 测试单边日期过滤
- 验证日期格式处理

#### 8. 排序功能 (test_list_entries_sorting)
- 测试升序和降序
- 测试不同排序字段（created_at/updated_at/title/status）
- 验证排序结果正确性

#### 9. 非法排序字段 (test_list_entries_invalid_sort_field)
- 验证非法字段回退到默认值
- 确保不抛出异常

#### 10. 组合过滤 (test_list_entries_combined_filters)
- 测试多个过滤条件同时应用
- 验证条件交集逻辑

#### 11. 边缘情况 (test_list_entries_edge_cases)
- 空标题处理
- 空密码处理
- Null值处理

#### 12. 标签列表 (test_get_distinct_tags)
- 验证返回不重复标签
- 确认排序正确

#### 13. 状态统计 (test_summaries_by_status)
- 验证各状态计数
- 确认总数正确

#### 14. 导出功能
- **test_prepare_export_rows_all_fields** - 导出所有字段
- **test_prepare_export_rows_selected_fields** - 导出指定字段
- **test_prepare_export_rows_with_filters** - 带过滤条件导出
- **test_prepare_export_rows_invalid_fields** - 非法字段抛出异常

### API层测试 (TestKnowledgeAPI)

#### 1. 认证测试
- **test_entries_without_auth** - 无认证返回401
- **test_entries_with_auth** - 有效认证返回数据

#### 2. 端点功能测试
- **test_entries_pagination** - 分页参数
- **test_entries_with_filters** - 过滤参数
- **test_tags_endpoint** - 标签列表端点
- **test_statuses_endpoint** - 状态统计端点

#### 3. 参数验证测试
- **test_entries_invalid_sort_field** - 非法排序字段返回400
- **test_entries_invalid_sort_order** - 非法排序方向返回400
- **test_entries_invalid_date_format** - 非法日期格式返回400

#### 4. CSV导出测试
- **test_export_csv** - 基础CSV导出
- **test_export_csv_with_fields** - 自定义字段导出
- **test_export_csv_with_filters** - 带过滤条件导出
- **test_export_csv_invalid_fields** - 非法字段返回400

#### 5. 详情页测试
- **test_entry_detail_not_found** - 不存在条目返回404

#### 6. 静态路由测试
- **test_kb_static_route** - 知识库UI路由

## 测试数据

### 测试数据库

测试使用临时SQLite数据库，每个测试类在 `setUpClass` 中创建临时目录，在 `tearDownClass` 中清理。

### 测试fixtures

#### 文章数据 (articles)
- art001 - https://lewz.cn/jprj/technology/article1 (technology标签)
- art002 - https://lewz.cn/jprj/business/article2 (business标签)
- art003 - https://lewz.cn/jprj/entertainment/article3 (entertainment标签)
- art004 - https://lewz.cn/jprj/article4 (未分类标签)
- art005 - https://lewz.cn/jprj/technology/article5 (空标题)

#### 链接数据 (extracted_links)
- 对应5篇文章的链接记录
- 涵盖所有状态：completed, pending, transferred, failed
- 包含完整链接、空链接、空密码等边缘情况

## 隔离性保证

### 临时数据库
- 使用 `tempfile.mkdtemp()` 创建唯一临时目录
- 每个测试类使用独立数据库文件
- 测试完成后自动清理

### 环境变量
- API测试通过环境变量设置数据库路径
- 使用测试专用的API密钥
- 不影响全局配置

### 数据隔离
- 每个测试方法前清空数据库
- 重新插入标准fixtures
- 测试间完全独立

## 最佳实践

### 添加新测试

1. 在适当的测试类中添加新方法
2. 方法名以 `test_` 开头
3. 使用 `self.assertEqual`, `self.assertIn` 等断言
4. 添加文档字符串说明测试目的

```python
def test_new_feature(self):
    """测试新功能的描述"""
    result = self.repo.new_method()
    self.assertEqual(result['status'], 'success')
```

### 测试边缘情况

确保测试覆盖：
- 空字符串
- Null值
- 超出范围的数值
- 非法格式输入
- 空列表/空结果

### 使用subTest

对于参数化测试，使用 `subTest` 提高可读性：

```python
for url, expected in test_cases:
    with self.subTest(url=url):
        result = self.repo.method(url)
        self.assertEqual(result, expected)
```

## CI/CD集成

测试可以轻松集成到CI/CD流程：

```yaml
# GitHub Actions示例
- name: Run knowledge module tests
  run: |
    cd wp
    python -m unittest tests.test_knowledge_module -v
```

## 故障排查

### 测试失败常见原因

1. **数据库未清理** - 确保每个测试前后正确清理
2. **路径问题** - 确认使用绝对路径或正确的相对路径
3. **环境变量冲突** - 检查是否有全局环境变量干扰
4. **依赖缺失** - 确保安装了所有测试依赖

### 调试技巧

```python
# 临时跳过测试
@unittest.skip("临时跳过")
def test_something(self):
    pass

# 只运行特定测试
if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromName('test_list_entries_basic')
    unittest.TextTestRunner(verbosity=2).run(suite)
```

## 性能考虑

- 测试使用SQLite内存模式可以提升速度
- 大量数据测试应该使用单独的性能测试文件
- 避免在测试中进行网络请求

## 相关文档

- [知识库API文档](../README_KNOWLEDGE_API.md)
- [知识库存储层文档](../README_KNOWLEDGE_REPO.md)
- [Python unittest文档](https://docs.python.org/3/library/unittest.html)
