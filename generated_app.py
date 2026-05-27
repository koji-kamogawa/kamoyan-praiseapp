import streamlit as st
import openai
import os
import json
import re

st.set_page_config(page_title="アプリ評価アプリ")

def read_uploaded_files(uploaded_files):
    contents = []
    for file in uploaded_files:
        try:
            content = file.getvalue().decode("utf-8")
            contents.append(f"--- {file.name} ---\n{content}")
        except UnicodeDecodeError:
            contents.append(f"--- {file.name} ---\n[バイナリファイルのため内容は読み取れません]")
    return "\n\n".join(contents)

def extract_title_from_script(content):
    """スクリプト内容からst.title()の引数を抽出する"""
    pattern = r"st\.title\(\s*['\"]([^'\"]+)['\"]\s*\)"
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return None

def call_deepseek(prompt):
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("環境変数 DEEPSEEK_API_KEY が設定されていません")
    client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        # model="deepseek-chat",
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": "あなたは親切でポジティブな評価者です。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

st.title("🌸アプリ評価アプリ")
st.write("あなたのアプリのスクリプトやデータファイルをアップロードし、「評価する」ボタンを押してください。")

uploaded_files = st.file_uploader(
    "ファイルをアップロード",
    accept_multiple_files=True,
    type=None
)

if "evaluate" not in st.session_state:
    st.session_state.evaluate = False
if "evaluation_text" not in st.session_state:
    st.session_state.evaluation_text = ""
if "extracted_title" not in st.session_state:
    st.session_state.extracted_title = None

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("評価する"):
        if uploaded_files and len(uploaded_files) > 0:
            st.session_state.evaluate = True
            st.session_state.evaluation_text = ""
            # アップロードされたスクリプトからタイトルを抽出
            for file in uploaded_files:
                try:
                    content = file.getvalue().decode("utf-8")
                    title = extract_title_from_script(content)
                    if title:
                        st.session_state.extracted_title = title
                        break
                except UnicodeDecodeError:
                    continue
        else:
            st.error("ファイルが1つもアップロードされていません。")
            st.session_state.evaluate = False

if st.session_state.evaluate and uploaded_files:
    with st.spinner("評価コメントを生成中..."):
        try:
            file_contents = read_uploaded_files(uploaded_files)
            prompt = f"""以下のアプリのスクリプトとデータファイルをもとに、アプリ開発者に対してポジティブな評価とアドバイスを200文字程度の日本語で作成してください。技術的な細かな指摘は不要です。励ましの言葉を含め、再度アプリを作りたくなるような内容にしてください。

ファイル内容:
{file_contents}"""
            result = call_deepseek(prompt)
            st.session_state.evaluation_text = result
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            st.session_state.evaluation_text = ""
    st.session_state.evaluate = False

# 抽出したタイトルを評価結果の前に表示
if st.session_state.extracted_title:
    st.markdown(f"### アプリのタイトル: {st.session_state.extracted_title}")

if st.session_state.evaluation_text:
    st.success("評価が完了しました！")
    st.markdown("### ☆彡あなたのアプリへの評価")
    st.markdown(st.session_state.evaluation_text)