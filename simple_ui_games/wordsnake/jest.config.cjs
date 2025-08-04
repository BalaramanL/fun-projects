
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  moduleNameMapper: {
    '\.(css|less)$_build': 'identity-obj-proxy'
  }
};

