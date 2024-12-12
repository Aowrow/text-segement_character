import os
import yaml
import requests
import time
from pathlib import Path

class TTSClient:
    def __init__(self, config_path):
        # 检查配置文件是否存在
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"找不到配置文件: {config_path}")
            
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 设置API基础URL
        self.base_url = f"http://{self.config['api']['host']}:{self.config['api']['port']}"
        
        # 创建输出目录
        Path(self.config['output']['dir']).mkdir(parents=True, exist_ok=True)
        
        print(f"已加载配置文件: {config_path}")

    def switch_models(self):
        """切换GPT和Sovits模型"""
        # 切换GPT模型
        response = requests.get(
            f"{self.base_url}/set_gpt_weights",
            params={"weights_path": self.config['models']['gpt_weights']}
        )
        if response.status_code != 200:
            raise Exception(f"切换GPT模型失败: {response.json()}")
        print("GPT模型切换成功")

        # 切换Sovits模型
        response = requests.get(
            f"{self.base_url}/set_sovits_weights", 
            params={"weights_path": self.config['models']['sovits_weights']}
        )
        if response.status_code != 200:
            raise Exception(f"切换Sovits模型失败: {response.json()}")
        print("Sovits模型切换成功")

    def text_to_speech(self, text, output_filename):
        """将文本转换为语音"""
        params = {
            "text": text,
            "text_lang": self.config['text']['language'],
            "ref_audio_path": self.config['models']['ref_audio'],
            "prompt_text": self.config['text']['prompt_text'],
            "prompt_lang": self.config['text']['prompt_language'],
            "text_split_method": self.config['text']['split_method'],
            "media_type": self.config['output']['format']
        }

        response = requests.get(f"{self.base_url}/tts", params=params)
        
        if response.status_code == 200:
            output_path = os.path.join(self.config['output']['dir'], output_filename)
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"已生成语音文件: {output_path}")
            return True
        else:
            print(f"生成语音失败: {response.json()}")
            return False

    def process_text_file(self):
        """处理输入文本文件"""
        try:
            # 读取输入文本文件
            with open(self.config['text']['input_file'], 'r', encoding='utf-8') as f:
                texts = f.readlines()

            # 处理每一行文本
            for i, text in enumerate(texts):
                text = text.strip()
                if text:  # 跳过空行
                    print(f"\n处理第 {i+1} 行文本: {text[:30]}...")
                    output_filename = f"output_{i+1}.{self.config['output']['format']}"
                    self.text_to_speech(text, output_filename)
                    time.sleep(1)  # 添加短暂延迟，避免请求太快

        except FileNotFoundError:
            print(f"找不到输入文件: {self.config['text']['input_file']}")
        except Exception as e:
            print(f"处理文件时出错: {str(e)}")

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='TTS客户端程序')
    parser.add_argument('-c', '--config', 
                      default='config.yaml',
                      help='配置文件路径 (默认: config.yaml)')
    args = parser.parse_args()

    try:
        # 实例化客户端
        client = TTSClient(args.config)
        
        # 切换模型
        print("正在切换模型...")
        client.switch_models()
        
        # 处理文本
        print("\n开始处理文本...")
        client.process_text_file()
        
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    main()