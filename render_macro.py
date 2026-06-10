import time
import pyautogui
import os
import subprocess

def render_capcut_project():
    """
    캡컷을 실행하고 완성된 프로젝트의 [내보내기] 버튼을 눌러 mp4로 렌더링하는 매크로입니다.
    (대장님 맞춤형: 바탕화면 바로가기 + 한글판 설정)
    """
    print("🎬 캡컷 렌더링 매크로 시작...")

    # 1. 캡컷 실행 (바탕화면 바로가기 사용)
    # 한글 윈도우 바탕화면 경로는 보통 둘 중 하나입니다.
    capcut_shortcut = r"C:\Users\User\Desktop\CapCut.lnk"
    
    if os.path.exists(capcut_shortcut):
        print("바탕화면에서 캡컷을 실행합니다...")
        os.startfile(capcut_shortcut)
    else:
        print("바탕화면에서 CapCut.lnk 바로가기를 찾을 수 없습니다. 경로를 확인해주세요.")
        return
    
    # 캡컷이 켜지고 프로젝트가 로드될 때까지 넉넉히 대기
    print("캡컷이 화면에 열리고 프로젝트를 불러오기를 기다립니다 (10초 대기)...")
    time.sleep(10)

    # 2. 내보내기 버튼 클릭 (한글판 단축키 활용)
    # 한글판 캡컷에서도 내보내기 단축키는 기본적으로 Ctrl + E 입니다.
    print("[내보내기] 창을 엽니다 (Ctrl + E)...")
    pyautogui.hotkey('ctrl', 'e')
    
    # 내보내기 창이 뜨는 시간 대기
    time.sleep(3)
    
    # 3. 렌더링 확정 (한글판 '내보내기' 파란색 버튼 클릭 효과)
    print("최종 렌더링을 시작합니다 (Enter)...")
    pyautogui.press('enter')

    print("✅ 렌더링 지시 완료! 동영상이 추출될 때까지 대기합니다.")
    
if __name__ == "__main__":
    render_capcut_project()
