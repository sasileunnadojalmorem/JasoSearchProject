import pymysql
import time
import tracemalloc
from jamo import h2j, j2hcj # 한글 자소 분해 라이브러리

# ==========================================
# 1. 자소 <-> 정수 매핑 딕셔너리 세팅
# ==========================================
JAMO_TO_INT = {
    'ㄱ': 1, 'ㄲ': 2, 'ㄴ': 3, 'ㄷ': 4, 'ㄸ': 5, 'ㄹ': 6, 'ㅁ': 7, 'ㅂ': 8, 'ㅃ': 9, 'ㅅ': 10, 
    'ㅆ': 11, 'ㅇ': 12, 'ㅈ': 13, 'ㅉ': 14, 'ㅊ': 15, 'ㅋ': 16, 'ㅌ': 17, 'ㅍ': 18, 'ㅎ': 19,
    'ㅏ': 20, 'ㅐ': 21, 'ㅑ': 22, 'ㅒ': 23, 'ㅓ': 24, 'ㅔ': 25, 'ㅕ': 26, 'ㅖ': 27, 'ㅗ': 28, 
    'ㅘ': 29, 'ㅙ': 30, 'ㅚ': 31, 'ㅛ': 32, 'ㅜ': 33, 'ㅝ': 34, 'ㅞ': 35, 'ㅟ': 36, 'ㅠ': 37, 
    'ㅡ': 38, 'ㅢ': 39, 'ㅣ': 40,
    'ㄳ': 41, 'ㄵ': 42, 'ㄶ': 43, 'ㄺ': 44, 'ㄻ': 45, 'ㄼ': 46, 'ㄽ': 47, 'ㄾ': 48, 'ㄿ': 49, 'ㅀ': 50, 'ㅄ': 51
}

# DB 연결 정보 (init_db.py와 동일)
DB_CONFIG = {
    'host': '127.0.0.1', 'port': 3306, 'user': 'root',
    'password': 'team_password', 'database': 'jaso_search', 'charset': 'utf8mb4'
}

# ==========================================
# 2. 데이터 처리 및 배열 변환 로직
# ==========================================
def char_to_jaso_array(char):
    """한 글자를 분해하여 자소에 해당하는 정수 1차원 배열로 반환합니다. (예: '가' -> [1, 20])"""
    jaso_str = j2hcj(h2j(char)) # '가' -> 'ㄱㅏ'
    return [JAMO_TO_INT.get(j, 0) for j in jaso_str if j in JAMO_TO_INT]

def text_to_3d_array(text):
    """게시글(텍스트)을 [단어[글자[자소]]] 형태의 3차원 정수 배열로 변환합니다."""
    words = text.split() # 띄어쓰기 단위로 단어 분리
    post_3d_array = []
    
    for word in words:
        word_2d_array = []
        for char in word:
            char_1d_array = char_to_jaso_array(char)
            if char_1d_array: # 특수기호나 공백 무시
                word_2d_array.append(char_1d_array)
        if word_2d_array:
            post_3d_array.append(word_2d_array)
            
    return post_3d_array

def load_data_from_db():
    """DB에서 1만 개의 데이터를 가져와 3차원 배열(전체는 4차원) 형태로 메모리에 적재합니다."""
    print("DB에서 데이터를 가져와 3차원 배열로 변환 중입니다...")
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT id, title, content FROM posts")
    rows = cursor.fetchall()
    
    db_memory = []
    for row in rows:
        # 제목과 본문을 합쳐서 하나의 3차원 배열로 만듭니다.
        full_text = f"{row['title']} {row['content']}"
        post_3d = text_to_3d_array(full_text)
        db_memory.append({"id": row['id'], "array_3d": post_3d})
        
    connection.close()
    return db_memory

# ==========================================
# 3. 베이스 코드 검색 로직 (완전 탐색 - Brute Force)
# ==========================================
def search_base_code(db_memory, search_query):
    """0차 알고리즘: 모든 문서를 4중 반복문으로 순회하며 자소 배열을 비교합니다."""
    # 1. 검색어도 똑같이 2차원 정수 배열로 변환합니다. (예: '가ㄱ' -> [[1, 20], [1]])
    query_2d = []
    for char in search_query:
        query_2d.append(char_to_jaso_array(char))
    # 비어있는 글자 제거 (예: 입력이 '가 ㄱ' 띄어쓰기가 들어갔을 경우)
    query_2d = [q for q in query_2d if q] 
    
    print(f"\n검색어 '{search_query}' -> 정수 배열 변환: {query_2d}")
    
    matched_doc_ids = []
    query_length = len(query_2d)
    
    # [시간 복잡도 측정 시작]
    start_time = time.perf_counter()
    
    # O(문서수 * 단어수 * 글자수 * 자소길이)의 최악의 완전 탐색 루프
    for doc in db_memory:                                 # 1. 문서 순회
        is_matched = False
        for word_2d in doc["array_3d"]:                   # 2. 문서 내 단어 순회
            # 단어 길이가 검색어 길이보다 짧으면 패스
            if len(word_2d) < query_length:
                continue
                
            for char_idx in range(len(word_2d) - query_length + 1):  # 3. 단어 내 글자 순회
                match_count = 0
                for q_idx in range(query_length):                    # 4. 검색어 글자 비교
                    doc_char_array = word_2d[char_idx + q_idx]
                    query_char_array = query_2d[q_idx]
                    
                    # [핵심] 검색어 자소가 문서 자소의 앞부분과 완벽히 일치하는지 확인
                    # 예: 문서 '가'(1,20) / 검색어 'ㄱ'(1) -> 매칭 성공!
                    if doc_char_array[:len(query_char_array)] == query_char_array:
                        match_count += 1
                    else:
                        break # 하나라도 틀리면 뒤에는 볼 필요 없음
                        
                if match_count == query_length:
                    is_matched = True
                    break
            
            if is_matched:
                break
                
        if is_matched:
            matched_doc_ids.append(doc["id"])

    # [시간 복잡도 측정 종료]
    end_time = time.perf_counter()
    elapsed_ms = (end_time - start_time) * 1000
    
    print(f"▶ 검색 완료! 총 {len(matched_doc_ids)}건 발견")
    print(f"▶ 검색 소요 시간: {elapsed_ms:.4f} ms")
    
    return matched_doc_ids

# ==========================================
# 4. 벤치마크 실행부 (공간/시간 복잡도 측정)
# ==========================================
if __name__ == "__main__":
    # [공간 복잡도 측정 시작] 메모리 추적기 가동
    tracemalloc.start()
    
    # 1. 데이터 적재
    db_memory = load_data_from_db()
    
    # [공간 복잡도 측정 종료]
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"\n[성능 지표] 1만 개 데이터 3차원 배열 변환 시 메모리 사용량")
    print(f"▶ 최대 메모리 점유율(공간 복잡도): {peak / 1024 / 1024:.2f} MB")
    
    # 2. 검색 테스트 케이스 실행
    # (예: '가' 치고 자음 'ㄱ'을 더 쳤을 때, '가구', '가방' 등이 정상 검색되는지 테스트)
    search_base_code(db_memory, "가ㄱ")
    search_base_code(db_memory, "팝ㄴ")