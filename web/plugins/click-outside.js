import Vue from 'vue'
import vClickOutside from 'v-click-outside'

Vue.use(vClickOutside)

Vue.directive('click-outside-2', {
  bind(el, binding, node) {
    el.clickOutsideEvent = function (event) {
      if (!(el === event.target || el.contains(event.target))) {
        node.context[binding.expression](event)
      }
    }
    document.body.addEventListener('click', el.clickOutsideEvent)
  },
  unbind(el) {
    document.body.removeEventListener('click', el.clickOutsideEvent)
  },
})
