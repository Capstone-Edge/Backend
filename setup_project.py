import os
import shutil

# 1. 생성할 디렉토리 구조 정의
dirs = [
    "app/api/v1",
    "app/services",
    "app/schemas",
    "app/core",
    "app/mcp"
]

# 2. 파일 이동 매핑 (기존 파일명: 새로운 경로)
file_mapping = {
    "main.py": "app/main.py",
    "device_state.py": "app/core/state_manager.py",
    "nlu_parser.py": "app/services/ai_service.py",
    "dialogue_manager.py": "app/services/dialogue_service.py",
    "mcp_server.py": "app/mcp/server.py"
}

def setup():
    # 폴더 생성 및 __init__.py 생성 (패키지화)
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "__init__.py"), "w") as f:
            pass
    
    if not os.path.exists("app/__init__.py"):
        with open("app/__init__.py", "w") as f:
            pass

    # 기존 파일 이동
    for src, dst in file_mapping.items():
        if os.path.exists(src):
            # 목적지 폴더가 없으면 생성
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            print(f"✅ 이동 완료: {src} -> {dst}")
        else:
            print(f"⚠️ 파일 없음: {src} (이미 이동되었거나 파일명이 다를 수 있습니다)")

    # 3. 새로운 뼈대 파일 생성 (비어있는 파일)
    new_files = [
        "app/api/v1/edge.py", 
        "app/schemas/edge_dto.py", 
        "app/api/v1/websocket.py"
    ]
    for f in new_files:
        if not os.path.exists(f):
            with open(f, "w") as file:
                pass
            print(f"✨ 신규 생성: {f}")

if __name__ == "__main__":
    setup()
    print("\n🚀 프로젝트 리팩토링 구조 생성이 완료되었습니다!")