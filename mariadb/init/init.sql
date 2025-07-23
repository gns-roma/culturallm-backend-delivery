CREATE DATABASE IF NOT EXISTS culturallm_db;
USE culturallm_db;

DROP USER IF EXISTS 'user'@'%';

CREATE USER 'user'@'%' IDENTIFIED BY 'userpassword';
GRANT ALL PRIVILEGES ON culturallm_db.* TO 'user'@'%' IDENTIFIED BY 'userpassword';
FLUSH PRIVILEGES;

-- UTENTI
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    nation VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    signup_date DATETIME NOT NULL,
    last_login DATETIME NOT NULL
);

-- LLMs
CREATE TABLE IF NOT EXISTS llms (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    name VARCHAR(255) NOT NULL UNIQUE
);

-- DOMANDE
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    llm_id INT,
    type ENUM('human', 'llm') NOT NULL DEFAULT 'human',
    question TEXT NOT NULL,
    topic VARCHAR(255) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (llm_id) REFERENCES llms(id) ON DELETE SET NULL
);

-- VALUTAZIONE DOMANDE
CREATE TABLE IF NOT EXISTS questions_evaluation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    llm_id INT NOT NULL,
    cultural_specificity INT NOT NULL DEFAULT 0 CHECK (cultural_specificity BETWEEN 0 AND 10),
    cultural_specificity_notes TEXT,
    coherence_qt BOOLEAN,
    UNIQUE(question_id, llm_id),
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (llm_id) REFERENCES llms(id) ON DELETE CASCADE
);

-- RISPOSTE
CREATE TABLE IF NOT EXISTS answers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    user_id INT,
    llm_id INT,
    type ENUM('human', 'llm') NOT NULL DEFAULT 'human',
    answer TEXT NOT NULL,
    UNIQUE (question_id, user_id),
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (llm_id) REFERENCES llms(id) ON DELETE SET NULL
);

-- VALUTAZIONE RISPOSTE
CREATE TABLE IF NOT EXISTS answers_evaluation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    answer_id INT NOT NULL,
    llm_id INT NOT NULL,
    validity INT NOT NULL DEFAULT 0 CHECK (validity BETWEEN 0 AND 5),
    validity_notes TEXT,
    coherence_qa BOOLEAN,
    UNIQUE(answer_id, llm_id),
    FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE CASCADE,
    FOREIGN KEY (llm_id) REFERENCES llms(id) ON DELETE CASCADE
);

-- RATING
CREATE TABLE IF NOT EXISTS ratings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    answer_id INT NOT NULL,
    question_id INT NOT NULL,
    user_id INT,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    flag_ia BOOLEAN NOT NULL,
    UNIQUE (question_id, user_id, answer_id),
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- LOGS
CREATE TABLE IF NOT EXISTS logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action_id INT NOT NULL,
    action_type VARCHAR(255) CHECK (action_type IN ('question', 'answer', 'rating', 'report', 'question_evaluation', 'answer_evaluation')),
    user_id INT,
    llm_id INT,
    question_id INT,
    answer_id INT,
    score INT NOT NULL DEFAULT 0,
    timestamp DATETIME NOT NULL,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (llm_id) REFERENCES llms(id) ON DELETE SET NULL
);

-- CLASSIFICA
CREATE TABLE IF NOT EXISTS leaderboard (
    user_id INT NOT NULL,
    score INT NOT NULL DEFAULT 0,
    num_ratings INT DEFAULT 0,
    num_questions INT DEFAULT 0,
    num_answers INT DEFAULT 0,
    UNIQUE (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- SEGNALAZIONI
CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    question_id INT,
    answer_id INT,
    reason TEXT,
    UNIQUE (user_id, question_id, answer_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE CASCADE
);

-- LLM Fittizio iniziale
INSERT INTO llms(name) VALUES("LLM_PLACEHOLDER");


-- view per ottenre la media delle valutazioni
CREATE OR REPLACE VIEW view_avg_answers_rating AS
SELECT avg(rating)
FROM ratings;

-- view per ottenere la media della cultural specificity delle domande per utente
CREATE OR REPLACE VIEW view_avg_cspecificity_per_user AS 
SELECT q.user_id, avg(qe.cultural_specificity)
FROM questions_evaluation AS qe LEFT JOIN questions AS q ON q.id = qe.question_id
GROUP BY (q.user_id);

-- view per ottenere la media della cultural specificity delle domande in generale
CREATE OR REPLACE VIEW view_avg_cspecificity AS 
SELECT avg(qe.cultural_specificity) AS average_cultural_specificity
FROM questions_evaluation AS qe;

-- view per ottenere il nuemro di risposte considerate cattive dalla IA 
-- per cattive si intende sotto le 2 stelle 
CREATE OR REPLACE VIEW view_percentage_of_bad_answers AS 
SELECT ( COUNT(CASE WHEN r.rating < 3 THEN 1 END) / COUNT(*) * 1.0 ) AS percentage
FROM ratings AS r;

-- view per ottenere il nuemro di risposte considerate cattive dalla IA  per utente
-- per cattive si intende sotto le 2 stelle 
CREATE OR REPLACE VIEW view_percentage_of_bad_answers_per_user AS 
SELECT r.user_id, ( COUNT(CASE WHEN r.rating < 3 THEN 1 END) / COUNT(*) * 1.0 ) AS percentage
FROM ratings AS r
GROUP BY (r.user_id);