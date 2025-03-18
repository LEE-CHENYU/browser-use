import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig

# Load environment variables
load_dotenv()

async def custom_agent_with_button_click():
    # Create browser configuration
    browser_config = BrowserConfig(
        headless=False  # Set to True in production
    )
    
    # Create browser instance
    browser = Browser(config=browser_config)
    
    # Create browser context with highlighting enabled
    context = BrowserContext(
        browser=browser, 
        config=BrowserContextConfig(
            highlight_elements=True,
            viewport_expansion=1000,  # Increased to try to include more elements
            cookies_file="temp_cookies.json"  # If you're using cookies
        )
    )
    
    # Define the resume file path
    resume_file_path = "/Users/chenyusu/Documents/GitHub/browser-use/李宸宇中文简历.docx"
    
    # Define the URL with proper escaping
    job_url = "https://q.yingjiesheng.com/jobdetail/158628025.html?property=%7B%22isInitiative%22%3A%22%E6%98%AF%22,%22isSuggest%22%3A%22%E5%90%A6%22,%22pageCode%22%3A%22recommend%7Crecommend%7Crecommendlb%22,%22requestId%22%3A%2202ef7bb8a8b336b833c35967a9dc4953%22,%22policyType%22%3A%22%E6%8E%A8%E8%8D%90%22,%22policyId%22%3A%22%7B%7D%22,%22jobSource%22%3A%22%E7%BD%91%E7%94%B3%22,%22jobId%22%3A%22158628025%22,%22jobTitle%22%3A%22%E6%A0%A1%E6%8B%9B%E8%81%8C%E4%BD%8D-%E6%88%98%E7%95%A5%E8%A7%84%E5%88%92%E5%B2%97%22,%22monthSalary%22%3A%2219-23%E4%B8%87%2F%E5%B9%B4%22,%22companyId%22%3A%228291041%22,%22companyName%22%3A%22%E5%95%86%E9%A3%9E%E6%99%BA%E8%83%BD%E6%8A%80%E6%9C%AF%22,%22jobRank%22%3A%222%22,%22jobType%22%3A%220%22,%22advId%22%3A%22%22,%22exrInfo02%22%3A%22%7B%5C%22retrieverName%5C%22%3A%5C%22DssmRetrievalService%5C%22,%5C%22referJobId%5C%22%3A%5C%22%5C%22,%5C%22intentions%5C%22%3A%5C%22%7BworkFunc%3D3304,%20workFuncStr%3D%E9%87%91%E8%9E%8E%2F%E7%BB%8F%E6%B5%8E%E7%A0%94%E7%A9%B6%E5%91%98,%20expectIndustry%3D00,%20expectWorkArea%3D020000,%20maxSalary%3D999999,%20seekType%3D0%7D%5C%22,%5C%22adExtendFunc%5C%22%3A%5C%22%5C%22,%5C%22adExtendCity%5C%22%3A%5C%22%5C%22,%5C%22recommendLabel%5C%22%3A%5C%22%5C%22,%5C%22workFuncMixedLabelResultExrInfo%5C%22%3A%5C%22%5C%22,%5C%22commonLabels%5C%22%3A%5B%5C%22%E5%90%8D%E4%BC%81%E6%A0%A1%E6%8B%9B%5C%22,%5C%22%E5%AD%A6%E6%A0%A1%E5%AD%A6%E5%8E%86%E5%8C%B9%E9%85%8D%E5%BA%A6%E9%AB%98%5C%22%5D%7D%22%7D&recommendReasons=%5B%22%E5%90%8D%E4%BC%81%E6%A0%A1%E6%8B%9B%22,%22%E5%AD%A6%E6%A0%A1%E5%AD%A6%E5%8E%86%E5%8C%B9%E9%85%8D%E5%BA%A6%E9%AB%98%22%5D"
    
    try:
        # Get a session and navigate to the URL
        session = await context.get_session()
        page = await context.get_current_page()
        
        print(f"Navigating to job listing...")
        await page.goto(job_url)
        
        # Wait for page to load
        await page.wait_for_load_state("networkidle")
        
        # Find and click the apply button directly
        print("Looking for the apply button...")
        
        # Try multiple possible selectors for the button
        apply_button = await page.query_selector('div.delivery-btn')
        if not apply_button:
            apply_button = await page.query_selector('button:has-text("立即申请")')
        if not apply_button:
            apply_button = await page.query_selector('a:has-text("立即申请")')
        if not apply_button:
            # Try a more generic approach
            await page.evaluate("""() => {
                const elements = Array.from(document.querySelectorAll('*'));
                for (const element of elements) {
                    if (element.textContent.trim() === '立即申请') {
                        element.style.border = '3px solid red';
                        element.click();
                        return true;
                    }
                }
                return false;
            }""")
        else:
            print("Apply button found, clicking...")
            await apply_button.click()
        
        # Wait a moment for any redirects or form loads
        await asyncio.sleep(2)
        
        # Now run the agent with further exploration instructions
        agent_task = f"""
    
    Complete the job application by navigating pages and filling the forms one by one with the following information, follow the sequence of the form, not the order of the following json. If encounter any information you don't have and please skip, if you can not skip please report:
    
    {{% IMPORTANT %}} If at any point there is a request to upload a resume or CV, please upload the file located at: {resume_file_path}
    
    {{% IMPORTANT %}} Look for any buttons or fields that require uploading a resume document and use the resume file provided. The application may require uploading this document as a mandatory step.
    
    {{% IMPORTANT %}} If a field is already filled with correct information, do not input anything in that field.
    
    {{
      "personal_info": {{
        "name": "李宸宇",
        "email": "451165547@qq.com",
        "linkedin": "CHENYU LI",
        "location": "纽约",
        "phone": "18652053798",
        "birth_date": "1998年9月18日",
        "github": "https://github.com/LEE-CHENYU",
        "linkedin_url": "linkedin.com/in/chenyu-li-50a81b156"
      }},
      "education": [
        {{
          "institution": "哥伦比亚大学",
          "degree": "应用分析 理学硕士",
          "location": "纽约",
          "period": "预计毕业时间：2023年2月",
          "courses": "研究设计、时间序列及人工智能；选修：盈利质量与基本面分析、并购会计、全球宏观政策、国际政治经济学",
          "projects": "为保险公司Pacific Life提款现金流搭建特征选择优化的SARIMAX时间序列预测模型"
        }},
        {{
          "institution": "上海交通大学",
          "degree": "日本语言文学 本科 第二专业：金融学",
          "gpa": "3.73/4.0",
          "location": "上海",
          "period": "2017年9月 – 2021年6月",
          "courses": "日语演讲比赛（A+）；日语精读（95/100）；微积分（91/100）；创业机会识别（96/100）；管理学（93/100）",
          "second_major": "金融学第二专业：宏微观经济学；计量经济学；公司金融；会计学；金融学；管理经济学"
        }},
        {{
          "institution": "早稻田大学商学院",
          "program": "学期交换留学",
          "location": "东京",
          "period": "2019年3月 - 2019年8月",
          "courses": "日本经济(A+)；日本商务实践；会计学(A)；金融学(A)；创业者素养讲座(A)；商务日语（A）；学术日语写作（A+）"
        }}
      ],
      "experience": [
        {{
          "company": "国盛证券",
          "position": "权益分析实习",
          "location": "上海",
          "period": "2021年10月 – 2021年11月",
          "responsibilities": [
            "运用Wind数据库拆解价值链并从公司盈利能力、产能方面对海信视讯科技有限公司2021年第三季度进行了全面的基本面分析",
            "熟练使用Python对团队的家电行业数据库进行更新、管理，从淘宝网提取、清理和分析季节性销售数据",
            "处理家电行业双十一销售数据，对数据进行归纳分析并总结出行业主要公司的大促时的产品结构和价格变化",
            "为导师的演讲路演总结分析结果，并制作decks（4份），有效地向利益相关者传达关键的见解和建议"
          ]
        }},
        {{
          "company": "南京证券",
          "position": "投行部实习",
          "location": "南京",
          "period": "2020年11月 – 2021年2月",
          "responsibilities": [
            "深度参与10亿元医药相关IPO项目",
            "撰写招股说明书底稿草稿（约30页），包括行业研究、市场分析、财务预测和管理团队介绍等部分",
            "与客户密切合作，进行了IPO项目前期行业与财务方面尽职调查，对比同业制药公司对关键指标包括收入、市盈率和EBITDA进行全面的财务分析，对研发费用、临床试验成功率和监管合规性等关键运营指标进行基准测试",
            "在尽职调查中提供了重要的支持，通过核实采购记录与银行流水，进行了库存检查和关联方查询，确保了尽职调查过程的准确性和完整性"
          ]
        }},
        {{
          "company": "毕马威华振会计师事务所",
          "position": "审计实习",
          "location": "南京",
          "period": "2020年1月",
          "responsibilities": [
            "参与沃得精工IPO审计；协助完成审计报告中所需细节性测试，利用Clara系统对2017以来三个财年的销售收入、应付职工薪酬、研发费用等科目的上千条凭证、帐户记录、销售发票和详细记录进行抽样测试",
            "参与先声药业年审；访谈客户人员，并审核先声药业集团提供的组织结构图，分析内部控制的有效性；协助完成银行存款、应付职工薪酬、固定资产等科目的审计底稿制作"
          ]
        }},
        {{
          "company": "中国工商银行",
          "position": "投资管理实习",
          "location": "南京",
          "period": "2019年8月-2019年10月",
          "responsibilities": [
            "理解并熟悉工商银行提供的资产管理产品，包括衍生品、固定收益和其他场外产品，对定价输入有深入认知",
            "协助设计和优化客户在保险、投资规划、现金管理和其他领域的策略，以帮助实现短期和长期的财务目标",
            "进行客户分析，以维护并扩展到全国的客户群；为来自不同领域的潜在客户设计促销活动",
            "定期审查和分析客户的投资组合和计划，以了解周期性或金融生命周期的重大变化，法律及形势问题，以及有利于改变投资管理战略的财务表现"
          ]
        }}
      ],
      "activities": [
        {{
          "organization": "上海交通大学21届北美校友会",
          "role": "理事",
          "location": "上海",
          "period": "2021年3月-至今",
          "description": "协助在美留学的400多名同学之间的沟通与互助；作为总负责人组织协调本届学生聚会，现已成功举办三次"
        }},
        {{
          "organization": "上海交通大学校董接待",
          "role": "陪同口译",
          "location": "上海",
          "period": "2019年11月",
          "description": "参与徐汇滨江开发区项目验收；协助院党委书记，为校董曹其镛及前日本首相麻生太郎胞弟麻生泰一行提供日汉口译"
        }},
        {{
          "organization": "贝恩杯案例咨询大赛",
          "role": "队长",
          "location": "上海",
          "period": "2019年5月",
          "description": "组建并领导团队；对中国轻奢珠宝行业进行市场分析，成果汇总为20页英文deck；利用财务数据、网络爬虫工具和可比公司分析进行了广泛的市场研究，以收集关于市场趋势、消费者行为和行业竞争力的见解；使用数据可视化工具（如think-cell）综合并展示了主要发现，强调了下沉市场的市场动态和消费趋势"
        }}
      ],
      "skills": {{
        "languages": [
          {{"language": "日语", "proficiency": "JLPT(N1)"}},
          {{"language": "英语", "proficiency": "IELTS（总分7.5；写作7）、GRE（330）"}},
          {{"language": "中文", "proficiency": "母语"}}
        ],
        "technical": [
          "R, STATA数据分析",
          "Bloomberg, Wind权益、固定收益分析",
          "熟练运用 Microsoft Word, PowerPoint, Excel",
          "Python编程",
          "PS, LR"
        ],
        "other": [
          "驾驶证：（C2）"
        ]
      }},
      "interests": "驾车环游过美国，并游历过欧盟十国；高中时曾作为外交代表团一员赴日本交流；通过实地亲身经历对秘鲁、墨西哥等发展中国家以及埃及、古巴等第三世界国家的政治、经济、社会环境建立了全面理解"
    }}
    
    Take screenshots of the completed application and report back when finished.
    """
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set the OPENAI_API_KEY environment variable")
        
        llm = ChatOpenAI(model="gpt-4o")
        
        agent = Agent(
            browser_context=context,
            task=agent_task,
            llm=llm,
            max_actions_per_step=4
        )
        
        print("Starting agent exploration...")
        result = await agent.run(max_steps=20)
        print(f"Agent completed with result: {result}")
        
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Keep browser open until user decides to close
        input("Press Enter to close the browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(custom_agent_with_button_click())