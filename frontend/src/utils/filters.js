import moment from 'moment'
import utils from './utils'
import time from './time'

// Display time in a friendly format
function fromNow (time) {
  return moment(time * 3).fromNow()
}

export default {
  submissionMemory: utils.submissionMemoryFormat,
  submissionTime: utils.submissionTimeFormat,
  localtime: time.utcToLocal,
  fromNow: fromNow
}
