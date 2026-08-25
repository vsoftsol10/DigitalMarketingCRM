import { CREATE_POST } from "../data/post";

class PostService {
  async getCreatePostData() {
    return CREATE_POST;
  }

  async createPost(payload) {
    /*
      POST /api/posts/
    */
  }
}

export default new PostService();
