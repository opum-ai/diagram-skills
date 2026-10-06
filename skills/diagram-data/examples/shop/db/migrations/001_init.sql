-- customers and orders
CREATE TABLE customers (
  id BIGSERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE orders (
  id BIGSERIAL PRIMARY KEY,
  customer_id BIGINT NOT NULL REFERENCES customers(id),
  total NUMERIC(10,2) NOT NULL,
  coupon_id BIGINT
);
CREATE TABLE products (id SERIAL PRIMARY KEY, sku TEXT NOT NULL UNIQUE, name TEXT);
CREATE TABLE order_items (
  order_id BIGINT NOT NULL,
  product_id INT NOT NULL,
  qty INT NOT NULL CHECK (qty > 0),
  PRIMARY KEY (order_id, product_id),
  CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES orders(id),
  FOREIGN KEY (product_id) REFERENCES products (id)
);
