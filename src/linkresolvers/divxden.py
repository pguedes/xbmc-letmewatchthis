'''
Created on May 31, 2010

@author: pedro
'''
from resolverUtils import processSourcePage
import string, re, logging

log = logging.getLogger("divxden")

FLV_MATCHER = '\("file","(.+)"\)'
FLV_MATCHER2 = "\\\\'file\\\\',\\\\'([^\\\\]+)\\\\'"

AVI_MATCHER = 'param name="src".?value="([^"]+)"'
PACKED_MATCHER = "eval\(function\(p,a,c,k,e,d\){.+}\('(.+)',(.+),(.+),'(.+)'.split\('\|'\)\)\)"

def resolve(page):
  def finder(streamsPage):
    found = re.compile(PACKED_MATCHER).findall(streamsPage)
    log.debug("Found packed code: %s" % str(found))
    p = found[0][0]
    a = int(found[0][1])
    c = int(found[0][2])
    k = found[0][3].split('|')
    unpacked = unpack(p, a, c, k)
    log.debug("Unpacked: %s" % str(unpacked))
    found = re.compile(FLV_MATCHER).findall(unpacked)
    if len(found) <= 0:
      log.debug("Using secondary .flv file pattern...")
      found = re.compile(FLV_MATCHER2).findall(unpacked)
    if len(found) <= 0:
      log.debug("Using .avi file pattern...")
      found = re.compile(AVI_MATCHER).findall(unpacked)
    log.debug("Links found: %s" % str(found))
    return found
  streams = processSourcePage(page, finder)
  log.debug("Streams found: %s" % str(streams))
  return streams

# This function is by Damon McCormick
# see: http://code.activestate.com/recipes/222109-radixstrnr-reverse-function-to-intsr-and-longsr/
def toRadixStr (number, radix, width=1,
          digits=string.digits + string.letters):
   """Inverse function to int(str,radix) and long(str,radix)."""
   digitCount = len(digits)
   if not 2 <= radix <= digitCount:
      raise ValueError, "radix must be in 2..%d" % digitCount
   result = []
   # convert some globals to locals for speed
   _divmod, _digits = divmod, digits
   append = result.append
   # check for a negative number
   if number < 0:
       number = -number
       isNegative = True
   else:
       isNegative = False
   # append digits in reverse order
   while number:
      (number, remainder) = _divmod(number, radix)
      append(_digits[remainder])
   # append leading 0s
   leading0s = digits[0] * (width - len(result)) # note: "0" * -1 == ''
   append(leading0s)
   # append sign if necessary and reverse
   if isNegative:
      append('-')
   result.reverse()
   return ''.join(result)

def unpack(p, a, c, k):
  while c > 0:
    c = c - 1
    if k[c]:
      pattern = "\\b%s\\b" % toRadixStr(c, a)
      p = re.sub(pattern, k[c], p)
  log.debug("Unpacked page code: %s" % p)
  return p
