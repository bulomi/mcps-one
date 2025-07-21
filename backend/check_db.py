import sqlite3

def check_database():
    try:
        conn = sqlite3.connect('data/mcps.db')
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("数据库中的表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 检查是否存在 mcp_tools 表
        if ('mcp_tools',) in tables:
            print("\nmcp_tools 表存在")
            # 获取表结构
            cursor.execute("PRAGMA table_info(mcp_tools);")
            columns = cursor.fetchall()
            print("mcp_tools 表结构:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
        else:
            print("\nmcp_tools 表不存在")
        
        conn.close()
        
    except Exception as e:
        print(f"检查数据库时出错: {e}")

if __name__ == "__main__":
    check_database()