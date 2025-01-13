use final_project;

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,  -- Contraseña sin encriptar (aunque deberías considerar encriptarla en producción)
    role VARCHAR(50) NOT NULL
);


ALTER TABLE users ADD COLUMN role_id INT, 
ADD FOREIGN KEY (role_id) REFERENCES roles(id);

drop table users

select * from users


