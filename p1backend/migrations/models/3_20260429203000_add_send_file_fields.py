from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sends" ADD "send_type" VARCHAR(16) NOT NULL DEFAULT 'text';
        ALTER TABLE "sends" ADD "file_name" VARCHAR(255);
        ALTER TABLE "sends" ADD "file_path" VARCHAR(500);
        ALTER TABLE "sends" ADD "file_size" BIGINT;
        ALTER TABLE "sends" ADD "file_mime_type" VARCHAR(255);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "sends" DROP COLUMN IF EXISTS "file_mime_type";
        ALTER TABLE "sends" DROP COLUMN IF EXISTS "file_size";
        ALTER TABLE "sends" DROP COLUMN IF EXISTS "file_path";
        ALTER TABLE "sends" DROP COLUMN IF EXISTS "file_name";
        ALTER TABLE "sends" DROP COLUMN IF EXISTS "send_type";"""


MODELS_STATE = (
    "eJztl21P2zAQx79KlFdMYgiy8qC9C10nOq3tBGGbQChyEze16tghdlYq1O8+n/OcPogiKq"
    "jUd/H/7uy7n+36+myG3MdUHN0KHJtfjWeToRCrj5p+aJgoikoVBImGVDsmykMraChkjDyp"
    "xBGiAivJx8KLSSQJZ0plCaUgck85EhaUUsLIY4JdyQMsxzqR+wclE+bjJyzyYTRxRwRTv5"
    "Yn8WFtrbtyFmmty+R37QirDV2P0yRkpXM0k2POCm/CJKgBZjhGEsP0Mk4gfcguKzOvKM20"
    "dElTrMT4eIQSKivlvpCBxxnwU9kIXWAAq3y2TlrnrYsvZ60L5aIzKZTzeVpeWXsaqAn0HX"
    "Ou7Uii1ENjLLmNSCykq0cL/NpjFC8HWI9qgFTpN0Hm2NaRzIUSZXl83ohliJ5cilkgx2p4"
    "cny8htxv+7p9ZV8fKK9PUA1XRzo96P3MZKU2wFvipOgVNGtBe5gFTBwiQjcBWQS8DcSt3+"
    "0aQuv09AUIlddKhNpWRxghIaY8XvLjuJpiNWY3T+NWUHoxhpJdJBdhflMWSUK8HGg9soHU"
    "z0KP8o8PCljV4A8YnWXXYA1fp9vr3Dh27xdUEgrxSDUi2+mAxdLqrKEenDW2opjE+NN1rg"
    "wYGneDfkcT5EIGsV6x9HPuTMgJJZK7jE9d5FdubK7mYGobm0T+Kze2Hrnf2HfdWJ089Iej"
    "SaXTAWGIvMkUxb67YOEWX+W7aAqtsKkghgK9K8AWsszaZRvHxBubSxrpzLK2lUalz76X3q"
    "Fe+p/6BwQpbfDWVkL2T20BEq7GBhAz990EuJXOWa0oMVvynv24GfRXNCllSAPkLVMF3vvE"
    "k4cGJUI+fEysayhC1bU3K4d30LP/Nrm2fw4um48RTHCpGL/r8zL/D0cCn/w="
)
