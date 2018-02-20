INSERT INTO user (
  username,
  email,
  pw_hash
)
VALUES
(
  "Kevin",
  "Kevin@Gmail.com",
  "pbkdf2:sha256:50000$KIaF8vKf$a39aac6a850d5c4c95c840bfd3763f1c71a63e181869dbbd5d4e2d73cf2828fb"
),
(
  "Thomas",
  "Thomas@Gmail.com",
  "pbkdf2:sha256:50000$KIaF8vKf$a39aac6a850d5c4c95c840bfd3763f1c71a63e181869dbbd5d4e2d73cf2828fb"
),
(
  "Billy",
  "Billy@Gmail.com",
  "pbkdf2:sha256:50000$KIaF8vKf$a39aac6a850d5c4c95c840bfd3763f1c71a63e181869dbbd5d4e2d73cf2828fb"
);

INSERT INTO message (
  author_id,
  text,
  pub_date
)
VALUES
(
  1,
  "Kevin's 1st post",
  1519031255
),
(
  1,
  "Kevin's 2nd post - fsdf",
  1519031320
),
(
  2,
  "Thomas's 1st post ",
  1519031252
),
(
  2,
  "Thomas's 2nd post ",
  1519031258
),
(
  3,
  "Billy's 1st post",
  1519031201
),
(
  3,
  "Billy's 2nd post",
  1519031207
);

INSERT INTO follower (
  who_id,
  whom_id
)
VALUES (
  1,
  2
),
(
  1,
  3
),
(
  3,
  2
),
(
  3,
  1
);
