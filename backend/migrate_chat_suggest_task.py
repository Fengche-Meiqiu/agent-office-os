"""
临时迁移脚本：给 chat_history 表添加 suggest_task 字段
小白解释：因为新增了 suggest_task 字段，老数据库需要补一列，不然查询会报错。
"""
from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///data/office.db', echo=False)
conn = engine.connect()
try:
    conn.execute(text('ALTER TABLE chat_history ADD COLUMN suggest_task BOOLEAN DEFAULT 0'))
    conn.commit()
    print('OK: suggest_task 字段已添加')
except Exception as e:
    if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
        print('OK: suggest_task 字段已存在')
    else:
        print(f'ERROR: {e}')
finally:
    conn.close()
