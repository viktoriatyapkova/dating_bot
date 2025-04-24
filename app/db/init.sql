CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR NOT NULL UNIQUE,
    name VARCHAR,
    age INTEGER,
    gender VARCHAR,
    interests TEXT,
    city VARCHAR,
    photo_url VARCHAR
);

CREATE TABLE IF NOT EXISTS user_likes (
    id SERIAL PRIMARY KEY,
    liker_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    liked_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    UNIQUE (liker_id, liked_id)  -- Запрещаем дублирующиеся лайки
);
