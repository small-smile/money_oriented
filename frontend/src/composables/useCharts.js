/* 图表实例的生命周期：init + setOption，resize 时重跑 build（原静态页 window.resize 的行为）。
 * 四个中国移动页原先各抄一份 mount/onResize，现在共用这一份；dispose 交给调用方的
 * onBeforeUnmount（各页原本就是这么写的，这里不改时机）。 */
import * as echarts from 'echarts'

export function useCharts() {
    const charts = []

    function mount(el, buildOption) {
        if (!el) return null
        const ins = echarts.init(el)
        ins.setOption(buildOption(ins), true)
        charts.push({ ins, build: buildOption })
        return ins
    }

    function onResize() {
        charts.forEach((c) => {
            c.ins.resize()
            c.ins.setOption(c.build(c.ins), true)
        })
    }

    function disposeAll() {
        charts.forEach((c) => {
            try {
                c.ins.dispose()
            } catch (_) {
                /* 已被 ECharts 自己清掉的实例再 dispose 会抛，忽略（与各页原写法一致） */
            }
        })
        charts.length = 0
    }

    return { charts, mount, onResize, disposeAll }
}
