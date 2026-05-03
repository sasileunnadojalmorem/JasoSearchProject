import pymysql
import random

# DB 연결 설정
db_config = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'team_password',
    'database': 'jaso_search',
    'charset': 'utf8mb4'
}

# 더미 데이터 생성을 위한 단어장
subjects = ["가방", "가구", "강아지", "고양이", "자전거", "노트북", "키보드", "마우스"]
verbs = ["팝니다", "삽니다", "교환해요", "나눔합니다", "추천해주세요", "어떤가요"]
adjectives = ["상태 좋은", "거의 새것", "급하게", "직거래만", "택배 가능"]

def generate_dummy_data(count=10000):
    print(f"[{count}개] 더미 데이터 생성 및 DB 삽입을 시작합니다...")
    
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    
    # 1. 테이블 생성 (기존 테이블 있으면 삭제)
    cursor.execute("DROP TABLE IF EXISTS posts;")
    create_table_query = """
    CREATE TABLE posts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        content TEXT NOT NULL
    )
    """
    cursor.execute(create_table_query)
    
    # 2. 1만 개 데이터 삽입 (Bulk Insert)
    insert_query = "INSERT INTO posts (title, content) VALUES (%s, %s)"
    data_to_insert = []
    
    for _ in range(count):
        title = f"[{random.choice(subjects)}] {random.choice(adjectives)} {random.choice(verbs)}"
        content = f"본문 내용입니다. {random.choice(subjects)} {random.choice(adjectives)} {random.choice(verbs)}. 연락주세요."
        data_to_insert.append((title, content))
        
    cursor.executemany(insert_query, data_to_insert)
    connection.commit()
    
    print("DB 초기화 및 데이터 삽입이 완료되었습니다!")
    cursor.close()
    connection.close()

if __name__ == "__main__":
    generate_dummy_data(10000)