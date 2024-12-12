import zhipuai
import json
import os
from api import api_key

class NovelAnalyzer:
    def __init__(self, api_key):
        self.client = zhipuai.ZhipuAI(api_key=api_key)
        self.system_prompt = """1. 识别文本中的所有角色(包括旁白)
2. 为所有文本找到说话的角色，不要因为句子中出现对应姓名就认为是说话人，要联系上下文判断。
3. 按照文章顺序为每一段内容标注序号（从1开始）,不要遗漏旁白的。
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
            # 将文本分成较小的段落
            text_segments = self._split_text(novel_text, max_length=1000)
            
            all_dialogues = []
            all_characters = set()
            dialogue_id = 1  # 用于跨段落保持ID连续
            
            # 逐段处理
            for i, segment in enumerate(text_segments):
                print(f"\n处理第 {i+1}/{len(text_segments)} 段...")
                
                response = self.client.chat.completions.create(
                    model="glm-4-long",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": segment}
                    ],
                    temperature=0.7,
                    top_p=0.7,
                    max_tokens=2048,
                    stream=False
                )
                
                # 解析响应
                content = response.choices[0].message.content
                cleaned_content = self._clean_json_content(content)
                result = json.loads(cleaned_content)
                
                # 更新对话ID以保持连续性
                for dialogue in result['dialogues']:
                    dialogue['id'] = dialogue_id
                    dialogue_id += 1
                
                # 合并结果
                all_characters.update(result['characters'])
                all_dialogues.extend(result['dialogues'])
            
            # 整理最终结果
            final_result = {
                "characters": list(all_characters),
                "dialogues": all_dialogues,
                "character_dialogues": {}
            }
            
            # 按角色整理对话
            for character in all_characters:
                character_dialogues = [
                    {"id": d["id"], "content": d["content"]}
                    for d in all_dialogues
                    if d["speaker"] == character
                ]
                final_result["character_dialogues"][character] = character_dialogues
            
            return final_result
                
        except Exception as e:
            print(f"API调用出错：{str(e)}")
            return None

    def _split_text(self, text, max_length=2000):
        """将文本分成较小的段落"""
        segments = []
        current_segment = []
        current_length = 0
        
        # 按句子分割
        sentences = text.split('。')
        
        for sentence in sentences:
            sentence = sentence.strip() + '。'
            if current_length + len(sentence) > max_length:
                segments.append(''.join(current_segment))
                current_segment = [sentence]
                current_length = len(sentence)
            else:
                current_segment.append(sentence)
                current_length += len(sentence)
        
        if current_segment:
            segments.append(''.join(current_segment))
        
        return segments

    def _clean_json_content(self, content):
        """清理API返回的JSON内容"""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

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
    
    parser = argparse.ArgumentParser(description='分析小说文本并提取对话')
    parser.add_argument('-i', '--input', default=r'E:\gpt-sovits\input\novel.txt',
                        help='输入文本文件路径 (默认: novel.txt)')
    parser.add_argument('-o', '--output', default=r"E:\gpt-sovits\output",
                        help='输出目录路径 (默认: output)')
    
    args = parser.parse_args()
    
    try:
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
            print(f"\n分析完成，结果已保存到目录：{args.output}")
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