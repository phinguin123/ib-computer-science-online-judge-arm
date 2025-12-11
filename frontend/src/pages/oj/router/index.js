import Vue from 'vue'
import VueRouter from 'vue-router'
import routes from './routes'
import storage from '@/utils/storage'
import {STORAGE_KEY} from '@/utils/constants'
import {sync} from 'vuex-router-sync'
import {types, default as store} from '../../../store'

Vue.use(VueRouter)

// Swallow the NavigationDuplicated error that Vue Router throws when pushing
// the same route, while still surfacing any other unexpected navigation errors.
const originalPush = VueRouter.prototype.push
VueRouter.prototype.push = function push (location, onResolve, onReject) {
  if (onResolve || onReject) {
    return originalPush.call(this, location, onResolve, onReject)
  }
  return originalPush.call(this, location).catch(err => {
    if (err && err.name !== 'NavigationDuplicated') {
      throw err
    }
    return err
  })
}

const originalReplace = VueRouter.prototype.replace
VueRouter.prototype.replace = function replace (location, onResolve, onReject) {
  if (onResolve || onReject) {
    return originalReplace.call(this, location, onResolve, onReject)
  }
  return originalReplace.call(this, location).catch(err => {
    if (err && err.name !== 'NavigationDuplicated') {
      throw err
    }
    return err
  })
}

const router = new VueRouter({
  mode: 'history',
  scrollBehavior (to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return {x: 0, y: 0}
    }
  },
  routes
})

// Global identity confirmation
router.beforeEach((to, from, next) => {
  Vue.prototype.$Loading.start()
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!storage.get(STORAGE_KEY.AUTHED)) {
      Vue.prototype.$error('Please login first')
      store.commit(types.CHANGE_MODAL_STATUS, {mode: 'login', visible: true})
      next({
        name: 'home'
      })
    } else {
      next()
    }
  } else {
    next()
  }
})

router.afterEach((to, from, next) => {
  Vue.prototype.$Loading.finish()
})

sync(store, router)

export default router
