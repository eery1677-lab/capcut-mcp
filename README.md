# 🎬 CapCut MCP Server (Upgraded by Antigravity)

이 프로젝트는 **CapCut Pro** 영상 편집을 AI 에이전트가 완벽하게 자동화할 수 있도록 지원하는 **Model Context Protocol (MCP)** 서버입니다. 기존 오픈소스 기반 위에 **우리 팀(Antigravity & Luca Agent)**의 필요에 맞춰 렌더링 파이프라인, 아시아권 폰트 지원 및 트랜지션 처리 로직을 대폭 업그레이드했습니다! 🚀

## ✨ 무엇이 업그레이드 되었나요? (Antigravity's Touch)

1. **VectCutAPI 안정성 극대화** 🛠️
   - Python 기반의 로컬 렌더링 서버인 `VectCutAPI`를 내장하고, `save_draft_impl.py` 등의 저장 로직을 개선하여 캡컷 초안(Draft)이 안전하게 사용자 폴더에 꽂히도록 수정했습니다.
2. **다국어(CJK) 폰트 완벽 지원** 🌏
   - 기본 `System` 폰트 에러를 해결하고, `SourceHanSansCN_Regular` 등 다국어/한글 지원 폰트를 매핑하여 자막 깨짐 없이 깔끔하게 출력되도록 폰트 엔진을 업그레이드했습니다.
3. **고급 트랜지션 및 키프레임 보강** 🌀
   - `Dissolve`, `Mix` 등 캡컷 고유의 대소문자 구분 트랜지션 에러를 해결하고, 줌인/줌아웃 등 `add_video_keyframe`을 활용한 미세 애니메이션 제어를 강화했습니다.
4. **유튜브 쇼츠 자동화 최적화** 📱
   - 9:16 비율(세로형) 렌더링 및 디졸브 트랜지션을 자동 적용하여 음원에 맞춰 이미지를 롤링하는 유튜브 파이프라인에 최적화되었습니다.

---

## 🚀 시작하기 (Installation & Setup)

CapCut MCP는 **2단계 구조**로 실행됩니다. Python 서버(VectCutAPI)가 캡컷 초안을 만들고, Node.js 서버(MCP)가 에이전트와 소통합니다.

### 1. Python 백엔드 실행 (VectCutAPI)
```bash
cd VectCutAPI
pip install -r requirements.txt
python capcut_server.py
```
> 기본적으로 `http://localhost:9000` (또는 9001)에서 대기합니다.

### 2. Node.js MCP 서버 연결
안티그래비티 `mcp_config.json`에 다음 설정을 추가하면 에이전트가 자동으로 인식합니다.
```json
{
  "mcpServers": {
    "capcut-mcp": {
      "command": "node",
      "args": ["C:/Users/User/Documents/capcut-mcp/dist/index.js"],
      "env": {
        "CAPCUT_API_URL": "http://localhost:9000"
      }
    }
  }
}
```

---

## 🛠️ 제공되는 도구 (Available Tools)

AI 에이전트는 다음 11가지 도구를 통해 비디오를 프로그래밍 방식으로 편집합니다.

1. **`capcut_create_draft`**: 새로운 프로젝트 초안 생성 (HD, 4K, 세로형 등)
2. **`capcut_add_video`**: 영상 추가 및 컷편집, 배속, 볼륨 조절
3. **`capcut_add_audio`**: 배경음악, BGM 및 페이드인/아웃 적용
4. **`capcut_add_text`**: 타이틀, 텍스트 추가 (색상, 그림자, 애니메이션)
5. **`capcut_add_image`**: 이미지 추가 및 배치 (크기, 회전)
6. **`capcut_add_subtitle`**: SRT 형식의 자막 자동 생성 및 싱크 매핑
7. **`capcut_add_keyframe`**: 부드러운 줌인/줌아웃 등 키프레임 애니메이션 생성
8. **`capcut_add_effect`**: 블러, 비네팅 등 화면 이펙트 추가
9. **`capcut_add_sticker`**: 스티커 및 이모지 삽입
10. **`capcut_save_draft`**: 완료된 프로젝트를 캡컷 데스크탑 앱으로 추출
11. **`capcut_get_duration`**: 영상/음원의 정확한 길이(메타데이터) 확인

---

## 📖 자동화 예시 (Workflow Example)

```python
# 에이전트 파이프라인 동작 예시
draft = req("/create_draft", {"width": 1080, "height": 1920}) # 세로형 쇼츠
req("/add_audio", {"draft_id": draft["draft_id"], "audio_url": "music.wav", "start": 0, "end": 60})
req("/add_image", {"draft_id": draft["draft_id"], "image_url": "scene.png", "transition": "Dissolve"})
req("/add_subtitle", {"draft_id": draft["draft_id"], "srt": "lyrics.srt", "font": "SourceHanSansCN_Regular"})
req("/save_draft", {"draft_id": draft["draft_id"]})
```

## 🙏 Acknowledgments
- Based on the original [VectCutAPI](https://github.com/sun-guannan/VectCutAPI) framework.
- Upgraded and Maintained by the **Antigravity & Luca Agent Team** for hyper-automated video production.
