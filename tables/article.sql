CREATE TABLE articles(
    id INT NOT NULL PRIMARY KEY AUTO_INCREMENT, 
    title VARCHAR(255) NOT NULL, 
    body VARCHAR(1000) NOT NULL, 
    author INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
    FOREIGN KEY (author) REFERENCES users(userid)
);

CREATE INDEX idx_articles_created ON articles(created_at);