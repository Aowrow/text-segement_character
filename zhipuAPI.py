import zhipuai
import json
import os
from api import api_key

class NovelAnalyzer:
    def __init__(self, api_key):
        self.client = zhipuai.ZhipuAI(api_key=api_key)  # 创建客户端实例
        
        # 系统预设提示
        self.system_prompt = """你现在要分析小说文本，需要完成以下任务：
1. 识别文本中的所有角色（包括旁白）
2. 找出每个角色说话的内容，不要因为句子中出现对应姓名就认为是说话人，要联系上下文判断。
3. 按照文章顺序为每一段内容标注序号（从1开始）,不要遗漏旁白的。注意，标注序号不需要一句一句标注，只要一段对话开始和结束时标注序号即可。
4. 按角色整理所有对话。
请以JSON格式输出，格式如下：
{
    "characters": ["角色1", "角色2", ...],
    "dialogues": [
        {"id": 1, "speaker": "角色1", "content": "对话内容"},
        ...
    ],
    "character_dialogues": {
        "角色1": [{"id": 1, "content": "对话内容"}, ...],
        "角色2": [{"id": 3, "content": "对话内容"}, ...]
    }
}"""

    def analyze_text(self, novel_text):
        try:
            # 1. 调用API获取响应
            response = self.client.chat.completions.create(
                model="glm-4-long",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": novel_text}
                ],
                temperature=0.7,
                top_p=0.7,
                max_tokens=2048, # 设置最大token数
                stream=False # 关闭流式输出
            )
            
            # 2. 收集完整的响应内容
            # full_content = ""
            # for chunk in response:
            #     if chunk.choices[0].delta.content is not None:
            #         full_content += chunk.choices[0].delta.content
            full_content = response.choices[0].message.content
            # 3. 打印原始响应，方便调试
            print("原始API响应内容：")
            print(full_content)
            
            # 4. 清理响应内容
            cleaned_content = full_content.strip()  # 去除首尾空白
            if cleaned_content.startswith("```json"):
                cleaned_content = cleaned_content[7:]  # 删除开头的```json
            if cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[:-3]  # 删除结尾的```
            cleaned_content = cleaned_content.strip()  # 再次去除可能的空白
            
            print("\n清理后的JSON内容：")
            print(cleaned_content)
            
            # 5. 解析JSON
            result = json.loads(cleaned_content)
            return result
            
        except Exception as e:
            print(f"API调用出错：{str(e)}")
            print("错误发生在处理响应内容时，请检查响应格式")
            return None

    def save_to_files(self, analysis_result, output_dir):
        if not analysis_result:
            return
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 为每个角色创建文件
        for character in analysis_result['characters']:
            character_dialogues = analysis_result['character_dialogues'].get(character, [])
            
            # 创建文件路径
            file_path = os.path.join(output_dir, f"{character}.txt")
            
            # 写入对话内容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"角色：{character}\n")
                f.write("=" * 30 + "\n")
                for dialogue in character_dialogues:
                    f.write(f"[{dialogue['id']}] {dialogue['content']}\n")

def main():
    import argparse
    
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='分析小说文本并提取对话')
    parser.add_argument('-i', '--input', default=r'E:\gpt-sovits\input\novel.txt',
                        help='输入文本文件路径 (默认: novel.txt)')
    parser.add_argument('-o', '--output', default=r"E:\gpt-sovits\output",
                        help='输出目录路径 (默认: output)')
    
    args = parser.parse_args()
    
    try:
        # 确保输出目录存在
        os.makedirs(args.output, exist_ok=True)
        
        # 读取文本文件
        with open(args.input, 'r', encoding='utf-8') as f:
            novel_text = f.read()
            
        # 创建分析器实例
        analyzer = NovelAnalyzer(api_key)
        
        # 分析文本
        result = analyzer.analyze_text(novel_text)
        
        if result:
            # 保存到文件
            analyzer.save_to_files(result, args.output)
            print(f"分析完成，结果已保存到目录：{args.output}")
            
            # 打印处理的对话数量
            print(f"共处理了 {len(result['dialogues'])} 条对话")
            print(f"识别出的角色：{', '.join(result['characters'])}")
        else:
            print("分析失败，未能生成结果")
        
    except FileNotFoundError:
        print(f"错误：找不到输入文件 {args.input}")
    except Exception as e:
        print(f"错误：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()