/** Links from the previous deployment used `/?p=/route&query`; send them to the canonical page. */
import { legacyTarget } from '../lib/routes';

const target = legacyTarget(window.location.search);
if (target) window.location.replace(target + window.location.hash);

export {};
