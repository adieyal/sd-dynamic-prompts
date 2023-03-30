module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: ["airbnb-base", "prettier"],
  plugins: ["prettier"],
  rules: {
    "class-methods-use-this": "off",
    "prettier/prettier": "error",
    curly: ["error", "all"],
    "no-console": "off",
  },
  parserOptions: {
    ecmaVersion: "latest",
  },
};
