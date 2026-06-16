import pandas as pd
import os

def create_sample_excel():
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Sample 1: 인구수 (Population)
    df_pop = pd.DataFrame({
        "지역명": ["서울", "부산", "대구", "인천", "광주", "대전", "울산"],
        "총인구수": [9400000, 3300000, 2300000, 2900000, 1400000, 1400000, 1100000],
        "남자인구": [4500000, 1600000, 1100000, 1450000, 690000, 690000, 560000],
        "여자인구": [4900000, 1700000, 1200000, 1450000, 710000, 710000, 540000]
    })
    df_pop.to_excel("data/인구수.xlsx", index=False)
    
    # Sample 2: 교통량 (Traffic)
    df_traffic = pd.DataFrame({
        "노선명": ["1호선", "2호선", "3호선", "4호선", "5호선", "6호선", "7호선", "8호선", "9호선"],
        "일평균승차인원": [320000, 1500000, 540000, 610000, 630000, 350000, 700000, 190000, 480000]
    })
    df_traffic.to_excel("data/지하철.xlsx", index=False)
    
    print("Sample Excel files created in backend/data/ folder.")

if __name__ == "__main__":
    create_sample_excel()
