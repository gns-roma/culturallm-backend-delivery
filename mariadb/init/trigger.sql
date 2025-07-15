USE culturallm_db;


DELIMITER //
CREATE OR REPLACE TRIGGER trg_leaderboard_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
  INSERT IGNORE INTO leaderboard (user_id, score, num_ratings, num_questions, num_answers)
  VALUES (NEW.id, 0, 0, 0, 0);
END;//
DELIMITER ;



DELIMITER //
CREATE OR REPLACE TRIGGER trg_logs_reports
AFTER INSERT ON reports
FOR EACH ROW
BEGIN
  if NEW.user_id IS NOT NULL THEN
    INSERT IGNORE INTO logs (user_id, score, action_type, timestamp)
    VALUES (NEW.user_id, 0, 'report', NOW());
  END IF;
END;//
DELIMITER ;




DELIMITER //
CREATE TRIGGER trg_logs_questions_update
AFTER UPDATE ON questions
FOR EACH ROW
BEGIN
  IF 
    NEW.cultural_specificity IS NOT NULL AND
    OLD.cultural_specificity IS NULL AND
    NEW.user_id IS NOT NULL
  THEN
    INSERT IGNORE INTO logs (user_id, score, action_type, timestamp)
    VALUES (NEW.user_id, NEW.cultural_specificity, 'question', NOW());
  END IF;
END;//
DELIMITER ;





DELIMITER //
CREATE OR REPLACE TRIGGER trg_logs_answer
AFTER INSERT ON answers
FOR EACH ROW
BEGIN
  IF NEW.user_id IS NOT NULL THEN
    INSERT IGNORE INTO logs (user_id, score, action_type, timestamp)
    VALUES (NEW.user_id, 0, 'answer', NOW());
  END IF;
END;//
DELIMITER ;


DELIMITER //
CREATE OR REPLACE TRIGGER trg_logs_ratings
AFTER INSERT ON ratings
FOR EACH ROW
BEGIN
  DECLARE answer_author INT DEFAULT NULL;
  DECLARE final_score   INT DEFAULT 0;

  SELECT user_id
  INTO answer_author
  FROM answers
  WHERE id = NEW.answer_id AND type = 'human'
  LIMIT 1;


  IF answer_author IS NOT NULL THEN
    SET final_score = NEW.rating;

    IF NEW.flag_ia = TRUE AND EXISTS (
      SELECT 1 FROM answers WHERE id = NEW.answer_id AND type = 'llm'
    ) THEN
      SET final_score = final_score + 1;
    ELSEIF NEW.flag_ia = FALSE AND EXISTS (
      SELECT 1 FROM answers WHERE id = NEW.answer_id AND type = 'human'
    ) THEN
      SET final_score = final_score + 1;
    END IF;

    INSERT INTO logs (user_id, score, action_type, timestamp)
    VALUES (answer_author, final_score, 'rating', NOW());
  END IF;
END;//
DELIMITER ;

DELIMITER //
CREATE OR REPLACE TRIGGER trg_leaderboard_update
AFTER INSERT ON logs
FOR EACH ROW
BEGIN
  UPDATE leaderboard
  SET score        = score + NEW.score,
      num_ratings  = num_ratings  + CASE WHEN NEW.action_type = 'rating'  THEN 1 ELSE 0 END,
      num_questions= num_questions+ CASE WHEN NEW.action_type = 'question' THEN 1 ELSE 0 END,
      num_answers  = num_answers  + CASE WHEN NEW.action_type = 'answer'  THEN 1 ELSE 0 END
  WHERE user_id = NEW.user_id;
END;//
DELIMITER ;
