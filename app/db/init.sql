--DROP TABLE IF EXISTS user_likes;
--DROP TABLE IF EXISTS user_profiles;


CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    telegram_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INTEGER NOT NULL CHECK (age BETWEEN 12 AND 100),
    gender VARCHAR(50) NOT NULL,
    interests TEXT,
    city VARCHAR(100) NOT NULL,
    photo_url TEXT NOT NULL,
    age_min INTEGER DEFAULT 18 CHECK (age_min BETWEEN 12 AND 100),
    age_max INTEGER DEFAULT 99 CHECK (age_max BETWEEN 18 AND 100),
    city_filter VARCHAR(100)  
);

CREATE TABLE user_likes (
    id SERIAL PRIMARY KEY,
    liker_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    liked_id INTEGER NOT NULL REFERENCES user_profiles(id) ON DELETE CASCADE,
    UNIQUE (liker_id, liked_id)
);


