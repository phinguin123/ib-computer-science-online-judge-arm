const localStorage = window.localStorage

export default {
  name: 'storage',

  /**
   * save value(Object) to key
   * @param {string} key Key
   * @param {Object} value Value
   */
  set (key, value) {
    localStorage.setItem(key, JSON.stringify(value))
  },

  /**
   * get value(Object) by key
   * @param {string} key Key
   * @return {Object}
   */
  get (key) {
    return JSON.parse(localStorage.getItem(key)) || null
  },

  /**
   * remove key from localStorage
   * @param {string} key Key
   */
  remove (key) {
    localStorage.removeItem(key)
  },
  /**
   * clear all
   */
  clear () {
    localStorage.clear()
  }
}
