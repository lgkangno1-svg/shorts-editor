# 한국어 YouTube 쇼핑쇼츠 500만+ 벤치마킹 연구

## 목적
한국어·한국 시청자 대상 쇼핑/상품소개형 YouTube Shorts 중 고성과 사례를 최소 100개 수집하고, 각 영상을 프레임·오디오·텍스트·썸네일 단위로 분석해 재현 가능한 제작 규칙을 도출한다.

## 우선 표본 기준
1. 한국어 내레이션 또는 한국어 자막 중심
2. 한국 시청자 대상 채널
3. 상품 소개·추천·시연·구매 유도 성격
4. 원칙적으로 조회수 5,000,000+ 우선
5. 500만+ 사례가 100개에 못 미칠 경우 300만+ 보조군을 별도 라벨로 분리하며 절대 혼합 집계하지 않음
6. 광고/브랜드 공식 CF는 기본 제외, 단 쇼핑쇼츠 제작 벤치마킹 가치가 높으면 `brand_official=true`로 별도 구분
7. 해외 원본 단순 번역·재편집은 `source_origin=overseas_remix`로 별도 구분

## 핵심 원칙
- 확인하지 못한 항목을 추측해 채우지 않는다.
- 각 필드에 `confirmed / estimated / unknown` 신뢰도를 붙인다.
- 폰트는 정확한 서체명이 확정되지 않으면 `고딕계열(추정)`처럼 기록한다.
- 효과음 역시 라이브러리 파일명을 확정할 수 없으면 기능적 유형(woosh, pop, click, impact 등)으로 기록한다.
- 조회수는 수집일에 따라 변하므로 `views_observed_at`와 함께 보관한다.
- 영상 URL과 썸네일 URL/참조를 모두 보존한다.

## 디렉터리
- `methodology/` : 표본선정·코딩 규칙·신뢰도 기준
- `data/` : CSV/JSONL 원자료
- `videos/` : 영상별 상세 분석 Markdown
- `thumbnails/` : 썸네일별 상세 분석 Markdown 및 참조 정보
- `reports/` : 100개 종합 통계, 패턴, 벤치마킹 가이드
- `sources/` : 공개 데이터 소스와 검증 로그

## 개별 영상 분석 필드
### 메타데이터
- video_id
- channel_name / channel_url
- shorts_url
- upload_date
- views / likes / comments (확인 가능한 경우)
- views_observed_at
- product/category
- shopping_method (YouTube Shopping / affiliate / external / unclear)

### 제목
- title_exact
- title_char_count_with_spaces
- title_char_count_without_spaces
- token/어절 수
- 숫자·가격·괄호·이모지·물음표·느낌표 사용
- 핵심 키워드 위치
- 제목 유형(문제해결/호기심/경고/비교/가격충격/전후/발견/리스트/후기 등)
- 영상 내용과 제목 일치도
- 제목이 약속한 payoff가 몇 초에 회수되는지

### 후킹
- 첫 음성 문장 원문
- 첫 화면 텍스트
- hook_start / hook_end
- hook_type
- 문제/손실회피/반전/가격충격/결과선공개/금지·경고/궁금증/사회적증거/전후비교 등
- 제품이 처음 등장하는 시점
- 핵심 효익이 처음 언급되는 시점

### 영상 구조
- total_duration_sec
- scene_count
- cut_timestamps
- avg_sec_per_cut
- median_sec_per_cut
- first_3s_cut_count
- first_5s_cut_count
- 화면전환 유형(hard cut, zoom, crop punch-in, whip, match cut, overlay 등)
- 구간별 내용: hook → problem → reveal → demo → proof → payoff → CTA
- 손/얼굴/제품 클로즈업 비중
- Before/After 여부
- 제품 패키지·가격·사용결과 노출 시간

### 오디오
- narration_type (human/AI/none/unclear)
- narration_speed 추정
- bgm_type
- sfx_types
- sfx_timestamps
- 효과음의 편집 기능(컷 강조/텍스트 등장/반전/제품 등장/CTA 등)
- 무음 또는 볼륨 드롭 구간

### 자막
- subtitle_position
- safe-area 위치
- lines_per_caption
- chars_per_caption 추정
- font_family_or_class
- font_weight
- font_size_relative_to_frame
- text_color
- outline_color / outline_width
- shadow
- background_box
- highlight_color
- keyword_emphasis
- word-by-word / phrase / full-sentence 방식
- 제품/손/얼굴과 겹침 여부

### 썸네일
- thumbnail_url_or_reference
- thumbnail_source (custom / selected frame / unknown)
- thumbnail_text_exact
- text_char_count
- text_position
- font_family_or_class
- font_weight
- font_size_relative
- text_color / outline / shadow / background
- product_position
- product_bbox_estimate (x,y,w,h %)
- product_frame_coverage_pct
- face_position / expression
- background_type / dominant palette
- before_after_layout
- arrows/circles/highlights
- negative_space
- visual_hierarchy
- title_thumbnail_semantic_relation
- thumbnail_video_first_frame_relation
- click_trigger 유형

### 벤치마킹 결론
- 왜 조회가 발생했을 가능성이 높은지
- 그대로 복제하면 안 되는 요소
- 구조만 차용할 요소
- 한국 쇼핑쇼츠 제작 시 적용 가능한 템플릿
- confidence / caveats

## 작업 위치
이 연구의 현재 기준 저장소는 `lgkangno1-svg/shorts-editor`이다.
