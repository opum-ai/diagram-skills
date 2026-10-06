CREATE TABLE coupons (id BIGSERIAL PRIMARY KEY, code TEXT UNIQUE);
ALTER TABLE orders ADD CONSTRAINT fk_coupon FOREIGN KEY (coupon_id) REFERENCES coupons(id);
CREATE TABLE legacy_carts (id INT);
DROP TABLE legacy_carts;
