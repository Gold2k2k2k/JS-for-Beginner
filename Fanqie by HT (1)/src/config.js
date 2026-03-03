let homepage = "https://fanqienovel.com";
let config_host = "https://fanqie.1415918.xyz";
let config_token = "encrypt_because_of_this";

if (typeof host !== "undefined") {
  config_host = host;
}

if (typeof token !== "undefined") {
  config_token = token;
}
if (typeof fq_token !== "undefined" && fq_token !== '""') {
  config_token = fq_token.replace(/^"(.*)"$/, "$1");
}

const hot_genres_url =
  "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index={{page}}&gender=-1&category_id={{category_id}}&creation_status=-1&word_count=-1&book_type=-1&sort=0";

let replaceCover = (u) => {
  if (u.startsWith("https://")) u = u.substring(8);
  else u = u.substring(7);
  let uArr = u.split("/");
  uArr[0] = "https://i0.wp.com/p6-novel.byteimg.com/origin";
  let uArr2 = [];
  uArr.forEach((x) => {
    if (!x.includes("?") && !x.includes("~")) uArr2.push(x);
    else uArr2.push(x.split("~")[0]);
  });
  u = uArr2.join("/");
  return u;
};
