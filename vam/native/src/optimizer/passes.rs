mod alias;
mod compress;
mod dead_shadow;
mod utils;

pub(super) use alias::observer_alias_pass;
pub(super) use compress::{compress_alias_pass, compress_idempotent_pass};
pub(super) use dead_shadow::dead_shadow_pass;
