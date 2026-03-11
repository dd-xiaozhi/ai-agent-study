import { defineConfig, presetUno, presetIcons, presetAttributify } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetIcons(),
    presetAttributify(),
  ],
  theme: {
    colors: {
      ink: {
        900: '#0a0a0a',
        800: '#1a1a1a',
        700: '#2a2a2a',
      },
      parchment: '#f0e6d2',
      crimson: '#8a1c1c',
      gold: '#c5a059',
    },
    fontFamily: {
      serif: '"Songti SC", "SimSun", serif',
      sans: '"PingFang SC", "Microsoft YaHei", sans-serif',
    },
  }
})
