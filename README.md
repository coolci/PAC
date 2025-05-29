根据以下三个文件设计一个爬虫，我只能提供一个大纲，你需要帮我分析对错，这大纲肯定有错误的地方，但是我需要你帮我总结和分析下，如何设计这个爬虫，并根据这些接口和大纲内容，如何写一下这个爬虫，并写一个实战案例的爬虫。模糊数据：# 政府采购数据管理系统技术文档

## 1. 系统概述

本系统是一个政府采购数据管理平台，提供数据采集、存储、检索和展示功能。系统基于Python Flask框架构建，使用SQLite数据库存储数据，提供RESTful API接口和Web前端界面。

## 2. 数据库初始化

### 2.1 初始化流程

```python
# 数据库初始化方法
init_db(load_sample_data=False)  # 默认不加载示例数据
```

### 2.2 初始化步骤

1. 检查数据库文件是否存在
2. 创建数据库表结构（通过config.py中的init_database函数）
3. 创建爬虫任务表（ensure_crawl_tasks_table函数）
4. 可选：加载示例数据（load_sample_data参数控制）
5. 初始化分类数据（check_and_update_categories函数）
6. 创建API统计表（ensure_api_stats_table函数）

### 2.3 手动加载示例数据

```
POST /api/load-sample-data
```

参数：
- force: Boolean，如果数据库中已有数据，是否强制覆盖

## 3. 数据采集功能

### 3.1 分类管理

#### 3.1.1 自动获取分类

系统启动时自动从政府采购网获取26个采购分类：
- 采购文件需求公示
- 资格预审公告
- 招标公告
- 非招标公告
- 更正公告
- 中标（成交）结果公告
- 等...

#### 3.1.2 手动更新分类

```
POST /api/categories/update
```

#### 3.1.3 定时更新分类

系统每天凌晨3点自动执行分类更新任务

### 3.2 爬虫任务管理

#### 3.2.1 触发爬虫任务

```
POST /api/crawl
```

参数：
- category: 分类名称
- categoryCode: 分类代码
- maxPages: 最大爬取页数
- saveDetails: 是否保存详情
- onlyNew: 是否只爬取新数据

#### 3.2.2 任务状态监控

```
GET /api/crawl-tasks
```

参数：
- limit: 最大返回任务数量

#### 3.2.3 中止任务

```
POST /api/crawl-tasks/{task_id}/abort
```

#### 3.2.4 删除任务

```
DELETE /api/crawl-tasks/{task_id}
```

#### 3.2.5 批量删除任务

```
POST /api/crawl-tasks/batch-delete
```

参数：
- taskIds: 任务ID数组
- status: 按状态筛选删除

#### 3.2.6 清理异常任务

```
POST /api/crawl-tasks/cleanup
```

## 4. 数据检索功能

### 4.1 基础搜索

```
GET /api/search
```

参数：
- keyword: 搜索关键词
- page: 页码
- pageSize: 每页记录数
- category: 分类
- searchContent: 是否搜索内容

特性：
- 支持标题、作者、项目名称、采购单位名称搜索
- 可选搜索文章内容
- 分页查询结果

### 4.2 政府采购高级搜索

```
POST /api/procurement/search
```

参数：
- title: 标题关键词
- author: 作者关键词
- publishDateStart: 发布开始日期
- publishDateEnd: 发布结束日期
- districtName: 区域名称
- procurementMethod: 采购方式
- projectName: 项目名称
- purchaseName: 采购单位名称
- budgetPriceMin: 预算金额下限
- budgetPriceMax: 预算金额上限
- supplierName: 供应商名称
- totalContractAmountMin: 合同金额下限
- totalContractAmountMax: 合同金额上限
- bidOpeningTimeStart: 开标开始时间
- bidOpeningTimeEnd: 开标结束时间
- limit: 返回数量限制
- offset: 偏移量

特性：
- 支持多条件组合检索
- 支持日期范围和金额范围筛选
- 支持文本模糊匹配和精确匹配

### 4.3 搜索选项获取

```
GET /api/procurement/search_options
```

返回内容：
- districtNames: 区域名称列表
- procurementMethods: 采购方式列表
- pathNames: 分类路径名称列表
- gpCatalogNames: 目录分类名称列表

## 5. 数据展示功能

### 5.1 文章列表

```
GET /api/articles
```

参数：
- category: 分类
- keyword: 关键词
- startDate: 开始日期
- endDate: 结束日期
- page: 页码
- pageSize: 每页记录数

### 5.2 文章详情

```
GET /api/article/{article_id}
```

返回内容：
- 文章基本信息
- 详情内容
- 附件列表

### 5.3 采购详情

```
GET /api/procurement/detail/{article_id}
```

返回内容：
- 采购基本信息
- 详情HTML内容
- 详情纯文本内容
- 附件列表
- 日期时间格式化

### 5.4 统计数据

```
GET /api/statistics
```

返回内容：
- totalArticles: 总文章数
- recentArticles: 最近7天文章数
- categories: 各分类文章数
- categoriesStats: 分类统计数据
- lastCrawl: 最近一次爬取时间
- detailCoverage: 详情覆盖率
- crawlProgress: 爬取进度

## 6. 数据导出功能

### 6.1 触发导出

```
POST /api/export
```

参数：
- category: 分类
- format: 导出格式(excel/markdown/both)
- details: 是否包含详情
- limit: 导出记录数量限制

### 6.2 下载导出文件

```
GET /api/download/{filename}
```

支持格式：
- Excel (.xlsx)
- Markdown (.md)

## 7. 数据清理功能

### 7.1 清空数据

```
POST /api/clear-data
```

参数：
- articles: 是否清空文章
- details: 是否清空详情
- tasks: 是否清空任务

## 8. API结构

### 8.1 系统内部API

#### 8.1.1 分类列表API

```
GET /api/categories
```

**响应示例：**
```json
{
  "success": true,
  "message": "获取分类列表成功",
  "data": [
    {
      "id": 1,
      "name": "采购意向",
      "categoryCode": "110-600268",
      "pathName": "采购意向公开",
      "totalRecords": 264257,
      "totalPages": 17618,
      "lastUpdate": "2025-05-30 03:49:26"
    },
    ...
  ],
  "total": 26
}
```

#### 8.1.2 文章列表API

```
GET /api/articles?category=采购意向&keyword=医疗&page=1&pageSize=20
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "total": 128,
    "page": 1,
    "pageSize": 20,
    "totalPages": 7,
    "articles": [
      {
        "id": 1,
        "article_id": "ZJ2025051200000012",
        "title": "杭州市第一人民医院采购意向",
        "author": "杭州市卫健委",
        "category": "采购意向",
        "path_name": "采购意向公开",
        "publish_date": "2025-05-12 10:30:00",
        ...
      },
      ...
    ]
  }
}
```

#### 8.1.3 政府采购高级搜索API

```
POST /api/procurement/search
```

**请求体示例：**
```json
{
  "title": "医疗设备",
  "publishDateStart": "2025-01-01",
  "publishDateEnd": "2025-05-30",
  "districtName": "杭州市",
  "procurementMethod": "公开招标",
  "budgetPriceMin": 100000,
  "budgetPriceMax": 1000000,
  "limit": 50,
  "offset": 0
}
```

**响应示例：**
```json
{
  "success": true,
  "total": 36,
  "data": [
    {
      "id": 125,
      "article_id": "ZJ2025031400000078",
      "title": "杭州市中医院医疗设备采购项目",
      "publish_date": "2025-03-14 09:15:00",
      "publish_date_formatted": "2025-03-14 09:15:00",
      "budget_price": 650000,
      ...
    },
    ...
  ]
}
```

### 8.2 官方API调用

#### 8.2.1 基础请求配置

```python
# 基础URL配置
BASE_URL = "https://zfcg.czt.zj.gov.cn"

# 请求头配置
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*"
}

# 使用requests.Session保持会话
session = requests.Session()
```

#### 8.2.2 获取分类结构

```python
# 获取分类结构API
def get_categories():
    url = f"{BASE_URL}/admin/category/home/categoryTreeFind"
    params = {
        "parentId": "600007",
        "siteId": "110"
    }
    
    response = session.get(url, params=params, headers=HEADERS, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("result") and data["result"].get("data"):
            structure_data = data["result"]["data"]
            categories = []
            
            # 解析分类树结构
            # 递归遍历分类树，提取叶子节点
            def traverse_categories(items, path_prefix=""):
                for item in items:
                    current_path = f"{path_prefix}{item['name']}" if path_prefix else item['name']
                    
                    # 只添加叶子节点作为分类
                    if not item.get("children") or len(item["children"]) == 0:
                        code = item["code"]
                        if not code.startswith("110-"):
                            category_code = f"110-{code}"
                        else:
                            category_code = code
                        
                        category = {
                            "name": item["name"],
                            "categoryCode": category_code,
                            "pathName": current_path
                        }
                        categories.append(category)
                    elif item.get("children"):
                        traverse_categories(item["children"], f"{current_path}/")
            
            if structure_data and isinstance(structure_data, list) and len(structure_data) > 0:
                root_item = structure_data[0]
                if root_item.get("children"):
                    traverse_categories(root_item["children"])
            
            return categories
    
    # 请求失败时返回预定义的静态分类列表
    return static_categories_list
```

#### 8.2.3 获取分类总记录数

```python
def get_category_total(category):
    url = f"{BASE_URL}/portal/category"
    post_data = {
        "pageNo": 1,
        "pageSize": 15,
        "categoryCode": category.get("categoryCode"),
        "isGov": True,
        "excludeDistrictPrefix": ["90", "006011"],
        "_t": int(time.time() * 1000),
        "isProvince": True
    }
    
    if "pathName" in category and category["pathName"]:
        post_data["pathName"] = category["pathName"]
    
    response = session.post(url, json=post_data, headers=HEADERS, timeout=30)
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "result" in data and "data" in data["result"]:
            total_records = data["result"]["data"].get("total", 0)
            total_pages = (total_records + 14) // 15  # 向上取整
            return total_records, total_pages
    
    return None, None
```

#### 8.2.4 获取分类页面数据

```python
def get_category_data(category, page_no):
    url = f"{BASE_URL}/portal/category"
    post_data = {
        "pageNo": page_no,
        "pageSize": 15,
        "categoryCode": category.get("categoryCode"),
        "isGov": True,
        "excludeDistrictPrefix": ["90", "006011"],
        "_t": int(time.time() * 1000),
        "isProvince": True
    }
    
    if "pathName" in category and category["pathName"]:
        post_data["pathName"] = category["pathName"]
    
    response = session.post(url, json=post_data, headers=HEADERS, timeout=30)
    return response.json() if response.status_code == 200 else None
```

#### 8.2.5 获取文章详情

```python
def get_article_detail(article_id):
    url = f"{BASE_URL}/portal/article/detail"
    post_data = {
        "articleId": article_id,
        "_t": int(time.time() * 1000)
    }
    
    response = session.post(url, json=post_data, headers=HEADERS, timeout=30)
    if response.status_code == 200:
        data = response.json()
        if data.get("success") and data.get("result"):
            return data["result"]
    
    return None
```

## 9. API统计与监控

### 9.1 API统计

```
GET /api/admin/stats
```

参数：
- days: 统计天数
- limit: 返回记录数限制

返回内容：
- 每个API端点的调用次数
- 每个API端点的平均响应时间
- 每个API端点的错误率

## 10. 数据库结构

### 10.1 主要表结构

- articles: 文章基本信息
- article_details: 文章详情
- categories: 分类信息
- crawl_tasks: 爬虫任务
- api_stats: API统计

### 10.2 关键字段

articles表：
- article_id: 文章ID
- title: 标题
- author: 作者
- category: 分类
- path_name: 路径名称
- publish_date: 发布日期
- project_name: 项目名称
- district_name: 区域名称
- purchase_name: 采购单位名称
- budget_price: 预算金额
- supplier_name: 供应商名称
- total_contract_amount: 合同总金额
- procurement_method: 采购方式
- bid_opening_time: 开标时间
- has_detail: 是否有详情

## 11. 系统部署与启动

### 11.1 启动服务器

```python
# 运行API服务器
app.run(host='0.0.0.0', debug=True)
```

### 11.2 系统配置

关键配置项：
- DB_PATH: 数据库文件路径
- 日志配置：级别、格式、存储路径

## 12. 错误处理与日志

### 12.1 日志配置

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_server.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
```

### 12.2 错误处理机制

- 数据库锁处理和重试机制
- API请求异常处理
- 爬虫进程异常处理

### 12.3 官方API错误处理

登录超时处理：

```python
if "login.timeout" in response_text:
    logger.warning("检测到登录超时错误，尝试使用portal API继续爬取...")
    # 切换到不需要登录的portal API
    return use_portal_api(category, page_no)
```

重试机制：

```python
max_retries = 3
retry_count = 0

while retry_count < max_retries:
    try:
        response = session.post(url, json=post_data, headers=HEADERS, timeout=30)
        # 处理响应...
        break
    except requests.exceptions.RequestException as e:
        retry_count += 1
        logger.warning(f"请求失败，正在进行第 {retry_count}/{max_retries} 次重试: {str(e)}")
        time.sleep(2)  # 等待2秒后重试
```

## 13. 前端界面

### 13.1 静态页面

- /procurement/: 政府采购首页
- /procurement/detail.html: 详情页面

### 13.2 Vue.js前端

- frontend/dist/: Vue.js构建后的前端应用
- 支持搜索、查看详情等功能

## 14. 官方API响应示例

### 14.1 分类结构响应

```json
{
  "success": true,
  "result": {
    "data": [
      {
        "id": 600007,
        "name": "政府采购",
        "code": "600007",
        "children": [
          {
            "id": 600268,
            "name": "采购意向",
            "code": "600268",
            "children": []
          },
          {
            "id": 424097,
            "name": "采购文件公示",
            "code": "424097",
            "children": []
          },
          // ... 更多分类
        ]
      }
    ]
  }
}
```

### 14.2 分类页面数据响应

```json
{
  "success": true,
  "result": {
    "data": {
      "records": [
        {
          "articleId": "ZJ2025051200000012",
          "title": "杭州市第一人民医院采购意向",
          "author": "杭州市卫健委",
          "publishDate": 1715474400000,
          "districtName": "杭州市",
          "projectName": "医疗设备采购项目",
          "purchaseName": "杭州市第一人民医院",
          "budgetPrice": 780000,
          "procurementMethod": "公开招标"
        },
        // ... 更多记录
      ],
      "total": 264257,
      "size": 15,
      "current": 1,
      "pages": 17618
    }
  }
}
```

### 14.3 文章详情响应

```json
{
  "success": true,
  "result": {
    "articleId": "ZJ2025051200000012",
    "title": "杭州市第一人民医院采购意向",
    "author": "杭州市卫健委",
    "publishDate": 1715474400000,
    "htmlContent": "<div>详细的采购意向内容...</div>",
    "textContent": "详细的采购意向内容...",
    "attachmentCount": 2,
    "districtName": "杭州市",
    "projectName": "医疗设备采购项目",
    "purchaseName": "杭州市第一人民医院",
    "budgetPrice": 780000,
    "procurementMethod": "公开招标"
  }
}
```

## 15. 系统性能优化

### 15.1 爬虫性能优化

- 使用守护线程运行后台任务
- 数据库连接超时设置
- 进程资源管理和清理

### 15.2 官方API访问优化

1. **请求频率限制**：系统实现请求间隔控制，避免触发官方网站的反爬机制
   ```python
   time.sleep(random.uniform(0.5, 1.5))  # 随机延迟0.5-1.5秒
   ```

2. **并发控制**：单线程顺序爬取，避免并发请求导致账号被封

3. **请求头模拟**：使用标准浏览器的User-Agent，避免被识别为爬虫

4. **错误恢复**：实现数据库事务和断点续传，确保爬取过程可中断可恢复

5. **数据校验**：爬取后对数据完整性进行校验，确保数据质量 



API案例第一份：# 浙江政府采购网站API分析

## 主要API

### 1. 列表数据API
- **URL**: `/portal/category`
- **方法**: POST
- **参数示例**:
```json
{
  "pageNo": 2,
  "pageSize": 15,
  "categoryCode": "110-600268",
  "isGov": true,
  "excludeDistrictPrefix": ["90", "006011"],
  "_t": 1748323359000,
  "isProvince": true,
  "districtCode": ["339900"]
}
```
- **响应示例**:
```json
{
  "success": true,
  "result": {
    "data": {
      "total": 33864,
      "data": [
        {
          "articleId": "5Gn8PpvGTWXGXmprc0ndGQ==",
          "annId": null,
          "siteId": 110,
          "firstCode": null,
          "parentId": null,
          "secondCode": null,
          "author": "浙江大学医学院附属儿童医院",
          "cover": null,
          "path": null,
          "pathName": "采购意向公开",
          "title": "浙江大学医学院附属儿童医院2025年5月三院区维修材料-工程政府采购意向",
          "content": null,
          "publishDate": 1748250241000,
          "districtCode": "339900",
          "gpCatalogCode": null,
          "gpCatalogName": "C99000000其他服务",
          "procurementMethodCode": null,
          "procurementMethod": null,
          "bidOpeningTime": null,
          "projectCode": null,
          "projectName": "三院区维修材料-工程类",
          "districtName": "浙江",
          "districtNameList": null,
          "purchaseName": "浙江大学医学院附属儿童医院",
          "rankCategoryName": null,
          "encryptId": null,
          "invalid": 0,
          "invalidDate": null,
          "isRenew": null,
          "announcementType": null,
          "ownerShotDepartmentName": null,
          "budgetPrice": "1200000.00",
          "supplierName": null,
          "totalContractAmount": null,
          "isReformation": null,
          "isReformationEnglishAnnouncement": null,
          "supportEnglish": null,
          "year": null,
          "monitorAmount": null,
          "smallAmount": null,
          "smallPercent": null
        },
        // ... 更多文章数据
      ],
      "empty": false
    }
  },
  "error": null
}
```
- **说明**: 此API用于获取公告列表数据，支持分页。返回的data数组中包含多个文章对象，每个对象包含articleId、title、publishDate等字段。

### 2. 详情页API
- **URL**: `/portal/detail`
- **方法**: GET
- **参数示例**: `articleId=5Gn8PpvGTWXGXmprc0ndGQ%3D%3D&timestamp=1748323370`
- **响应示例**:
```json
{
  "success": true,
  "result": {
    "data": {
      "title": "浙江大学医学院附属儿童医院2025年5月三院区维修材料-工程政府采购意向",
      "htmlTitle": null,
      "isCustomTitle": 0,
      "articleId": "5Gn8PpvGTWXGXmprc0ndGQ==",
      "siteId": 110,
      "author": "浙江大学医学院附属儿童医院",
      "projectCode": null,
      "projectName": "三院区维修材料-工程类",
      "publishDate": 1748250241000,
      "documentNo": null,
      "redHeadFile": null,
      "rankCategoryName": null,
      "belongingName": "",
      "implementationDate": null,
      "announcementType": 10016,
      "announcementId": "oO6DaUeZPYV1+7FkwP7VmITwhJI3yMqKEmeFXDD+K4I=",
      "isGovPurchase": false,
      "districtCode": "339900",
      "isGovernmentPurchaseService": 1,
      "categoryNames": ["采购公告","政府采购公告","采购意向","采购意向公开"],
      "isShowAttachment": false,
      "subscriptionUrl": null,
      "supportEnglish": null,
      "englishTitle": null,
      "announcementLinkDtoList": null,
      "content": "<style id=\"fixTableStyle\" type=\"text/css\">th,td {border:1px solid #DDD;padding: 5px 10px;}</style> \n<meta charset=\"utf-8\"> \n<div id=\"template-center-mark\"> \n <style id=\"template-center-style-mark\">#template-center-mark .selectTdClass{background-color:#edf5fa !important}\n#template-center-mark ol,#template-center-mark ul{margin:0;pading:0;width:95%}...",
      "click": 110,
      "attachmentList": [],
      "attachmentVO": null,
      "dynamicNodeLinkList": null,
      "expireFlag": 0,
      "expiredAt": "2025-06-05T15:59:59.000+0000",
      "challengeLink": null,
      "projectProcurementFlag": null,
      "announcementShowVo": null,
      "newLinkNodeList": null
    }
  },
  "error": null
}
```
- **说明**: 此API用于获取公告详细内容。返回数据中包含完整的文章信息，其中content字段是HTML格式的公告正文内容。

### 3. 其他辅助API
- **初始化API**: `/api/polaris/global/init`
  - **响应示例**:
  ```json
  {
    "success": true,
    "result": {
      "polaris": {
        "version": "x.x.x",
        "config": {
          // 网站配置信息
        }
      }
    },
    "error": null
  }
  ```

- **风险评估API**: `https://aggregated.zcygov.cn/api/service/risk/common/business/process/tree`
  - **响应示例**:
  ```json
  {
    "success": true,
    "result": {
      "data": [
        // 风险评估树形结构数据
      ]
    },
    "error": null
  }
  ```

- **无障碍服务API**: `/api/services/Accessibility/Client/pc`
  - **响应示例**:
  ```json
  {
    "success": true,
    "result": {
      // 无障碍服务配置
    },
    "error": null
  }
  ```

## 左侧分类及参数说明

### 获取不同分类的方法

浙江政府采购网左侧菜单包含多个分类，所有分类数据都通过同一个API接口获取：

- **URL**: `https://zfcg.czt.zj.gov.cn/portal/category`
- **方法**: POST

### 分类结构

通过对网站的分析，网站左侧菜单包含以下主要分类：

- 采购意向
- 采购意向公开
- 意见征询
- 采购项目公告
- 更正公告
- 采购结果公告
- 采购合同公告
- 履约验收公告
- 电子卖场公告
- 框架协议公告
- 政府采购监管公告
- 其他政府采购公告
- 质疑回复公告
- 非政府采购公告

### categoryCode参数获取方法

`categoryCode`是区分不同类型公告的关键参数，获取方法有以下几种：

1. **通过网络请求分析**:
   - 使用浏览器开发者工具的网络面板
   - 在网站上点击左侧不同分类
   - 观察发送到`/portal/category`的请求
   - 从请求体中提取`categoryCode`参数

2. **通过URL参数提取**:
   - 注意网页URL中的`parentId`和`childrenCode`参数
   - `categoryCode`通常采用格式`siteId-childrenCode`
   - 示例：URL中的`childrenCode=600268`对应请求中的`categoryCode=110-600268`

3. **通过响应数据反推**:
   - 首次请求某个分类后，记录响应中所有文章的`pathName`值
   - 使用该`pathName`值构造新的请求
   
### 分类与对应参数值

下表展示了主要分类及其对应的参数：

| 分类名称 | pathName参数值 | categoryCode值(示例) |
|---------|---------------|-------------------|
| 采购意向 | 采购意向公开 | 110-600268 |
| 采购项目公告 | 招标公告、非招标公告 | 110-ZcyAnnouncement |
| 更正公告 | 更正公告 | 110-ZcyModifyAnnouncement |
| 采购结果公告 | 中标公告、成交公告 | 110-ZcyAwardAnnouncement |
| 采购合同公告 | 采购合同公告 | 110-ZcyContractAnnouncement |
| 履约验收公告 | 履约验收公告 | 110-ZcyAcceptanceAnnouncement |

> 注意：实际的categoryCode值需要通过抓包确认，上表仅提供格式参考。

### 请求不同分类的完整参数示例

```json
{
  "pageNo": 1,
  "pageSize": 15,
  "categoryCode": "110-600268",  // 采购意向对应的分类代码
  "pathName": "采购意向公开",     // 对应的分类名称
  "isGov": true,
  "excludeDistrictPrefix": ["90", "006011"],
  "_t": 1748323359000,           // 当前时间戳
  "isProvince": true,
  "districtCode": ["339900"]     // 可选，筛选特定地区
}
```

### 爬取多个分类的实现思路

1. 维护一个分类代码映射表，包含所有分类的`categoryCode`和`pathName`
2. 遍历每个分类
3. 构造对应的请求参数
4. 发送请求获取数据
5. 解析响应中的`articleId`等关键信息
6. 根据需要使用`articleId`获取详情内容
7. 存储数据到JSON或Excel

### 示例代码框架

```python
# 分类映射表
CATEGORIES = [
    {"name": "采购意向", "categoryCode": "110-600268", "pathName": "采购意向公开"},
    {"name": "采购项目公告", "categoryCode": "110-ZcyAnnouncement", "pathName": "招标公告"},
    {"name": "更正公告", "categoryCode": "110-ZcyModifyAnnouncement", "pathName": "更正公告"},
    # 其他分类...
]

# 遍历所有分类
for category in CATEGORIES:
    page_no = 1
    while True:
        params = {
            "pageNo": page_no,
            "pageSize": 15,
            "categoryCode": category["categoryCode"],
            "pathName": category["pathName"],
            "isGov": True,
            "excludeDistrictPrefix": ["90", "006011"],
            "_t": int(time.time() * 1000),
            "isProvince": True
        }
        
        response = requests.post("https://zfcg.czt.zj.gov.cn/portal/category", json=params)
        data = response.json()
        
        # 处理数据...
        articles = data["result"]["data"]["data"]
        for article in articles:
            article_id = article["articleId"]
            # 存储或进一步获取详情...
        
        # 判断是否有下一页
        if page_no * 15 >= data["result"]["data"]["total"]:
            break
        
        page_no += 1
```

## categoryCode参数说明

`categoryCode`是区分不同类型公告的关键参数：
- 此参数值来源于网站URL中的`childrenCode`参数
- 不同类型的公告对应不同的categoryCode值
- 示例：
  - "110-600268": 采购意向公开
  - "110-175885": 可能是其他类型的公告

## 获取所有articleId的方法

1. 发送POST请求到`/portal/category`接口
2. 请求参数中使用目标公告类型的`categoryCode`值
3. 通过修改`pageNo`参数遍历所有页面
4. 从返回的JSON数据中提取所有文章的`articleId`字段
5. 可以使用这些articleId通过详情页API获取完整内容

## 示例请求流程

1. **获取列表数据**:
```
POST /portal/category
Content-Type: application/json

{
  "pageNo": 1,
  "pageSize": 15,
  "categoryCode": "110-600268",
  "isGov": true,
  "excludeDistrictPrefix": ["90", "006011"],
  "_t": 1748323359000,
  "isProvince": true,
  "districtCode": ["339900"]
}
```

实际获取到的响应:
```json
{
  "success": true,
  "result": {
    "data": {
      "total": 33864,  // 总记录数
      "data": [
        {
          "articleId": "5Gn8PpvGTWXGXmprc0ndGQ==",  // 文章ID，用于获取详情
          "title": "浙江大学医学院附属儿童医院2025年5月三院区维修材料-工程政府采购意向",
          "author": "浙江大学医学院附属儿童医院",
          "publishDate": 1748250241000,  // 发布时间戳
          "projectName": "三院区维修材料-工程类",
          "budgetPrice": "1200000.00"
          // ... 其他字段
        },
        // ... 更多文章
      ]
    }
  }
}
```

2. **获取详情数据**:
```
GET /portal/detail?articleId=5Gn8PpvGTWXGXmprc0ndGQ%3D%3D&timestamp=1748323370
```

实际获取到的响应:
```json
{
  "success": true,
  "result": {
    "data": {
      "title": "浙江大学医学院附属儿童医院2025年5月三院区维修材料-工程政府采购意向",
      "articleId": "5Gn8PpvGTWXGXmprc0ndGQ==",
      "author": "浙江大学医学院附属儿童医院",
      "publishDate": 1748250241000,
      "content": "<style id=\"fixTableStyle\" type=\"text/css\">th,td {border:1px solid #DDD;padding: 5px 10px;}</style>...",  // HTML格式的正文
      "attachmentList": [],  // 附件列表
      "expiredAt": "2025-06-05T15:59:59.000+0000"  // 过期时间
    }
  }
}
```

## 实现爬虫的建议

1. 使用分页机制爬取所有列表页
2. 提取每篇文章的articleId
3. 访问详情页API获取完整内容
4. 处理并存储数据（如JSON或Excel格式）
5. 考虑添加请求延迟、随机UA、代理IP等措施避免被封 ，案例第二份：# 浙江政府采购网API接口分析

## 基础信息

- 网站地址：https://zfcg.czt.zj.gov.cn/site/category
- 基础API路径：https://zfcg.czt.zj.gov.cn

## 主要API接口

### 1. 分类树结构

**接口**：`/admin/category/home/categoryTreeFind`

**请求方式**：GET

**参数**：
- `parentId`: 父级分类ID，如 `600007`（采购公告）
- `siteId`: 站点ID，固定为 `110`
- `timestamp`: 时间戳

**示例**：
```
https://zfcg.czt.zj.gov.cn/admin/category/home/categoryTreeFind?parentId=600007&siteId=110&timestamp=1748350083
```

**返回数据**：包含分类树结构的JSON数据

### 2. 列表数据

**接口**：`/portal/category`

**请求方式**：POST

**请求体**：
```json
{
  "pageNo": 1,
  "pageSize": 15,
  "categoryCode": "110-175885",
  "isGov": true,
  "excludeDistrictPrefix": ["90", "006011"],
  "_t": 1748350546000
}
```

**参数说明**：
- `pageNo`: 页码，从1开始
- `pageSize`: 每页条数
- `categoryCode`: 分类代码
- `isGov`: 是否政府采购
- `excludeDistrictPrefix`: 排除的行政区划前缀
- `_t`: 时间戳

**可选过滤参数**：
- `keyword`: 关键词
- `publishDateRange`: 发布日期范围，包含 `startDate` 和 `endDate`
- `districtCode`: 行政区划代码
- `procurementMethodCode`: 采购方式代码

**返回数据**：包含列表数据的JSON，主要数据在 `result.data.data` 数组中

### 3. 详情数据

**接口**：`/portal/detail`

**请求方式**：GET

**参数**：
- `articleId`: 文章ID
- `timestamp`: 时间戳

**示例**：
```
https://zfcg.czt.zj.gov.cn/portal/detail?articleId=LUtehfU%2FWLOd5oDu1KOC2g%3D%3D&timestamp=1748350343
```

**返回数据**：包含详情数据的JSON，主要数据在 `result.data` 对象中

### 4. 采购方式列表

**接口**：`/magic/front/service/static/zcy.secondpagesearchlist.purchaseMode/api`

**请求方式**：GET

**参数**：
- `timestamp`: 时间戳

**示例**：
```
https://zfcg.czt.zj.gov.cn/magic/front/service/static/zcy.secondpagesearchlist.purchaseMode/api?timestamp=1748350083
```

**返回数据**：包含采购方式列表的JSON数据

### 5. 行政区划列表

**接口**：`/api/core/getSubDistrictByPid`

**请求方式**：GET

**参数**：
- `pId`: 父级行政区划ID，如 `953`（浙江省）
- `timestamp`: 时间戳

**示例**：
```
https://zfcg.czt.zj.gov.cn/api/core/getSubDistrictByPid?pId=953&timestamp=1748350083
```

**返回数据**：包含行政区划列表的JSON数据

## 常用分类代码

- `110-175885`：采购意向
- `110-978863`：采购项目公告
- `110-908841`：采购结果公告
- `110-424097`：单一来源采购公示
- `110-988011`：采购文件需求公示

## 数据结构

### 列表数据字段

- `articleId`: 文章ID
- `title`: 标题
- `publishDate`: 发布日期（时间戳）
- `districtCode`: 行政区划代码
- `districtName`: 行政区划名称
- `gpCatalogName`: 采购目录名称
- `projectName`: 项目名称
- `purchaseName`: 采购单位名称
- `budgetPrice`: 预算金额
- `author`: 发布者

### 详情数据字段

- `title`: 标题
- `content`: 内容（HTML格式）
- `publishDate`: 发布日期（时间戳）
- `author`: 发布者
- `projectCode`: 项目编号
- `projectName`: 项目名称
- `documentNo`: 文号
- `isShowAttachment`: 是否显示附件
- `announcementType`: 公告类型

## 请求头

```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36
Content-Type: application/json;charset=UTF-8
Accept: application/json, text/plain, */*
Origin: https://zfcg.czt.zj.gov.cn
Referer: https://zfcg.czt.zj.gov.cn/site/category
```
