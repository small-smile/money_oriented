import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import configPrettier from 'eslint-config-prettier'
import globals from 'globals'

// 工程护栏：ESLint(flat) + eslint-plugin-vue，与 Prettier 分工（格式交给 prettier，规则不冲突）。
// legacy/ 是逐字复制的原始全局脚本（window.* / 裸 echarts），不纳入 lint。
export default [
  { ignores: ['dist/**', 'node_modules/**', 'src/views/company/bank/legacy/**'] },
  js.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: { ...globals.browser },
    },
    rules: {
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrors: 'none' }],
      // 本项目大量用全角空格「　」做标题/标签分隔，属有意为之，模板/字符串里放行。
      'no-irregular-whitespace': ['error', { skipStrings: true, skipTemplates: true, skipComments: true }],
      'vue/multi-word-component-names': 'off',
    },
  },
  configPrettier,
]
