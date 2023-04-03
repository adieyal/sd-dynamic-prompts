module.exports = {
  env: {
    browser: true,
    es2021: true,
  },
  extends: ["airbnb-base", "prettier"],
  plugins: ["prettier"],
  rules: {
    "class-methods-use-this": "off",
    "max-classes-per-file": "off",
    "no-console": "off",
    "no-param-reassign": "off",
    "prettier/prettier": "error",
    curly: ["error", "all"],
  },
  parserOptions: {
    ecmaVersion: "latest",
  },
};
