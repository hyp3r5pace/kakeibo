-- Dropping exisiting tables (useful for development when you want to reset)

DROP TABLE IF EXISTS expenses;
DROP TABLE IF EXISTS user_categories;
DROP TABLE IF EXISTS system_categories;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    created_at DATE DEFAULT CURRENT_DATE
);

CREATE TABLE user_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
    system_category_id INTEGER,
    user_category_id INTEGER,
    description TEXT,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (system_category_id IS NULL AND user_category_id IS NULL) OR
        (system_category_id IS NULL AND user_category_id IS NOT NULL) OR
        (system_category_id IS NOT NULL AND user_category_id IS NULL)
    ),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (system_category_id) REFERENCES system_categories(id) ON DELETE SET NULL,
    FOREIGN KEY (user_category_id) REFERENCES user_categories(id) ON DELETE SET NULL
);


-- Initialize system_categories with seed value
INSERT INTO system_categories (name, display_name) VALUES
('SALARY', 'salary'),
('RENT', 'rent'),
('UTILITIES', 'utilities'),
('GROCERY', 'grocery'),
('EMI', 'emi'),
('TRANSPORT', 'transport'),
('FREELANCE', 'freelance'),
('INVESTMENT', 'investment'),
('INVESTMENT RETURN', 'investment return'),
('SHOPPING', 'shopping'),
('SUBSCRIPTION', 'subscription'),
('REMITTANCE SENT', 'remittance sent'),
('REMITTANCE RECEIVED', 'remittance received'),
('LEISURE', 'leisure'),
('MEDICAL', 'medical');


-- Doing essential indexing for now
-- Further indexing will be done once app basic operations are built and database queries are decided
CREATE INDEX index_user_categories_user_id ON user_categories(user_id);
CREATE INDEX index_expenses_user_date_id ON expenses(user_id, date DESC, id DESC);


