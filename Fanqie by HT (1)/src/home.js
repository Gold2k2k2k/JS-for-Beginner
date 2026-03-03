function execute() {
  return Response.success([
    {
      title: "巅峰榜",
      input: "https://fanqienovel.com/api/author/misc/top_book_list/v1",
      script: "gen.js",
    },
    {
      title: "最热",
      input:
        "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index={{page}}&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0",
      script: "gen.js",
    },
    {
      title: "最新",
      input:
        "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index={{page}}&gender=-1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=1",
      script: "gen.js",
    },
    {
      title: "最新已完结",
      input:
        "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index={{page}}&gender=-1&category_id=-1&creation_status=0&word_count=-1&book_type=-1&sort=1",
      script: "gen.js",
    },
    {
      title: "最热短篇小说",
      input:
        "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index={{page}}&gender=-1&category_id=-1&creation_status=0&word_count=0&book_type=-1&sort=0",
      script: "gen.js",
    },
    {
      title: "男生",
      input:
        "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index={{page}}&gender=1&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0",
      script: "gen.js",
    },
    {
      title: "女生",
      input:
        "https://fanqienovel.com/api/author/library/book_list/v0/?page_count=18&page_index={{page}}&gender=0&category_id=-1&creation_status=-1&word_count=-1&book_type=-1&sort=0",
      script: "gen.js",
    },
    {
      title: "出版",
      input:
        "https://fanqienovel.com/api/node/publication/list?page_index={{page}}&page_count=18",
      script: "gen.js",
    },
  ]);
}
